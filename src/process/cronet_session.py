import csv
import json

from process import constant_converter
from process.quic_session import QuicConnection

IGNORE_DOMAIN_NAME_LIST = ['google.com','googleapis.com','doubleclick.net','google-analytics.com']

class CronetSession:
    def __init__(self,session_start_time, data_converted_path , filename_without_ext):
        self.session_start_time = session_start_time
        self.event_list = []
        self.data_converted_path = data_converted_path
        self.filename_without_ext = filename_without_ext
        self.source_dns_dict = {} # key: source id, value: event list belong to the source id
        self.source_quic_dict = {}  # key: source id, value: event list

    def add_event(self, cronet_event):
        cronet_event.time_elaps = cronet_event.time_int - self.session_start_time
        self.event_list.append(cronet_event)

        #group dns events
        if cronet_event.source_type == 'HOST_RESOLVER_IMPL_JOB':
            if cronet_event.source_id in self.source_dns_dict.keys():
                self.source_dns_dict[cronet_event.source_id].append(cronet_event)
            else:
                self.source_dns_dict[cronet_event.source_id] = [cronet_event]

        #group quic events
        if cronet_event.source_type == 'QUIC_SESSION':
            if cronet_event.source_id in self.source_quic_dict.keys():
                self.source_quic_dict[cronet_event.source_id].append(cronet_event)
            else:
                self.source_quic_dict[cronet_event.source_id] = [cronet_event]

    def save(self):
        with open(self.data_converted_path + self.filename_without_ext + '.csv', 'wt') as f:
            cw = csv.writer(f)
            cw.writerow(['time', 'time_elaps','event_type','source_id','source_type','phase','source_dependency_id','source_dependency_type','other_data'])
            for c_event in self.event_list:
                cw.writerow(c_event.get_info_list())

    #match dns and quic session
    def match_dns_quic_session(self):
        dns_dict = {} # key: domain, value: (start_time, end_time)
        for source_id , event_list in self.source_dns_dict.items():
            host = None
            dns_begin_time = None
            dns_end_time = None
            for cronet_event in event_list:
                if cronet_event.event_type == 'HOST_RESOLVER_IMPL_JOB' and cronet_event.phase == 'PHASE_BEGIN':
                    host = cronet_event.other_data['params']['host']
                    dns_begin_time = cronet_event.time_int
                elif cronet_event.event_type == 'HOST_RESOLVER_IMPL_JOB' and cronet_event.phase == 'PHASE_END':
                    dns_end_time = cronet_event.time_int


            else:
                dns_dict[host] = (dns_begin_time, dns_end_time)


        quic_session_dict = {}  # key: host, value: tuple(source id, quic session event)
        for source_id, event_list in self.source_quic_dict.items():
            try:
                host = event_list[0].other_data['params']['host']
                #check ignore list
                ignore = False
                for ignore_host in IGNORE_DOMAIN_NAME_LIST:
                    if ignore_host in host:
                        ignore = True
                        break
                if ignore:
                    print('WARN: quic session source id', source_id, 'host', host, 'was ignored due to IGNORE list')
                    continue

                if host not in dns_dict.keys():
                    print('WARN: quic session source id', source_id,'has no dns record, add dummy one')
                    dns_dict[host] = (event_list[0].time_int, event_list[0].time_int)
                source_id =  event_list[0].source_id
                if host in quic_session_dict.keys():
                    quic_session_dict[host].append((source_id, event_list))
                else:
                    quic_session_dict[host] = [(source_id, event_list)]
            except BaseException as e:
                print('processing session ( source id =', source_id,') failed with exception:"', e.message , '", session skipped')

        return dns_dict, quic_session_dict


    def create_quic_session(self):
        json_files = []

        dns_dict, quic_session_dict = self.match_dns_quic_session()
        for host, quic_session_group_list in quic_session_dict.items():
            dns_begin_time, dns_end_time = dns_dict[host]
            for (source_id, event_list) in quic_session_group_list:
                if event_list:
                    print('processing quic session data, host:', host, ', source id:', source_id, ', event start absloute time:', constant_converter.get_readable_time(event_list[0].time_int))
                    quic_session = QuicConnection(host, dns_begin_time, dns_end_time, event_list, self.data_converted_path, self.filename_without_ext)
                    json_files.append(quic_session.save())

        return json_files


class CronetEvent():
    def __init__(self,event_log_obj):
        self.time_int = int(event_log_obj['time'])
        self.time_elaps = 0
        self.event_type = constant_converter.get_event_type(event_log_obj['type'])
        self.source_id = event_log_obj['source']['id']
        self.source_type = constant_converter.get_source_type(event_log_obj['source']['type'])
        self.phase = constant_converter.get_phase(event_log_obj['phase'])
        self.source_dependency_id = 'N/A'
        self.source_dependency_type = 'N/A'
        other_event = event_log_obj.copy()
        if 'params' in other_event.keys() and 'source_dependency' in other_event['params'].keys():
            self.source_dependency_id = other_event['params']['source_dependency']['id']
            self.source_dependency_type = constant_converter.get_source_type(other_event['params']['source_dependency']['type'])
            del other_event['params']['source_dependency']
        del other_event['time']
        del other_event['type']
        del other_event['source']
        self.other_data = other_event
        self.other_data_str = json.dumps(self.other_data)

    def get_info_list(self):
        return [self.time_int, self.time_elaps, self.event_type, self.source_id, self.source_type, self.phase,self.source_dependency_id , self.source_dependency_type ,self.other_data_str]


if __name__ == '__main__':
    event_log_str = '{"params":{"new_config":{"auto_detect":true}},"phase":0,"source":{"id":7,"type":0},"time":"87726889","type":27}'
    event_log_obj = json.loads(event_log_str)
    event = CronetEvent(event_log_obj)
    print(event.get_info_list())