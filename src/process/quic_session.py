import csv

from process import constant_converter
from process.quic_connection import QuicConnection

IGNORE_DOMAIN_NAME_LIST = ['google.com','googleapis.com','doubleclick.net','google-analytics.com']

class QuicSession:
    def __init__(self,session_start_time, data_converted_path , filename_without_ext):
        self.session_start_time = session_start_time
        self.event_list = []
        self.data_converted_path = data_converted_path
        self.filename_without_ext = filename_without_ext
        self.source_quic_dict = {}  # key: source id, value: event list

    def add_event(self, cronet_event):
        cronet_event.time_elaps = cronet_event.time_int - self.session_start_time
        self.event_list.append(cronet_event)

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



class ClientQuicSession(QuicSession):
    def __init__(self,session_start_time, data_converted_path , filename_without_ext):
        QuicSession.__init__(self,session_start_time, data_converted_path , filename_without_ext)
        self.source_dns_dict = {} # key: source id, value: event list belong to the source id

    def add_event(self, cronet_event):
        QuicSession.add_event(self, cronet_event)

        #group dns events
        if cronet_event.source_type == 'HOST_RESOLVER_IMPL_JOB':
            if cronet_event.source_id in self.source_dns_dict.keys():
                self.source_dns_dict[cronet_event.source_id].append(cronet_event)
            else:
                self.source_dns_dict[cronet_event.source_id] = [cronet_event]


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


    def create_quic_connection(self):
        json_files = []

        dns_dict, quic_session_dict = self.match_dns_quic_session()
        if len(quic_session_dict)==0:
            print('no quic session found')
        for host, quic_session_group_list in quic_session_dict.items():
            dns_begin_time, dns_end_time = dns_dict[host]
            for (source_id, event_list) in quic_session_group_list:
                if event_list:
                    print('processing quic session data, host:', host, ', source id:', source_id, ', event start absloute time:', constant_converter.get_readable_time(event_list[0].time_int))
                    quic_connection = QuicConnection(host, dns_begin_time, dns_end_time, event_list, self.data_converted_path, self.filename_without_ext)
                    json_files.append(quic_connection.save())

        return json_files


class ServerQuicSession(QuicSession):
    def __init__(self,session_start_time, data_converted_path , filename_without_ext):
        QuicSession.__init__(self,session_start_time, data_converted_path , filename_without_ext)

    #match dns and quic session
    def get_quic_session_dict(self):
        quic_session_dict = {"host":[]}  # key: host, value: tuple(source id, quic session event)
        for source_id, event_list in self.source_quic_dict.items():
            try:
                source_id = event_list[0].source_id
                quic_session_dict["host"].append((source_id, event_list))
            except BaseException as e:
                print('processing session ( source id =', source_id,') failed with exception:"', e.message , '", session skipped')
        return quic_session_dict


    def create_quic_connection(self):
        json_files = []

        quic_session_dict = self.get_quic_session_dict()
        if len(quic_session_dict)==0:
            print('no quic session found')
        for host, quic_session_group_list in quic_session_dict.items():
            for (source_id, event_list) in quic_session_group_list:
                if event_list:
                    print('processing quic session data, host:', host, ', source id:', source_id, ', event start absloute time:', constant_converter.get_readable_time(event_list[0].time_int))
                    quic_connection = QuicConnection(host, self.session_start_time, self.session_start_time, event_list, self.data_converted_path, self.filename_without_ext)
                    json_files.append(quic_connection.save())

        return json_files

