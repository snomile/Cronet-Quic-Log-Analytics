import csv
import json
import time

import constant_converter


class ChromeSession:
    def __init__(self,session_start_time,persistant_file_path):
        self.session_start_time = session_start_time
        self.event_list = []
        self.persistant_file_path = persistant_file_path

    def add_event(self,chrome_event):
        chrome_event.time_elaps = chrome_event.time_int - self.session_start_time
        self.event_list.append(chrome_event)

    def save(self):
        with open(self.persistant_file_path, 'wt') as f:
            cw = csv.writer(f)
            for c_event in self.event_list:
                cw.writerow(c_event.get_info_list())


class ChromeEvent():
    def __init__(self,event_log_obj):
        self.time_int = int(event_log_obj['time'])
        self.time_elaps = 0
        #time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.time_int))
        self.event_type = constant_converter.get_event_type(event_log_obj['type'])
        self.source_id = event_log_obj['source']['id']
        self.source_type = constant_converter.get_source_type(event_log_obj['source']['type'])

        other_event = event_log_obj.copy()
        del other_event['time']
        del other_event['type']
        del other_event['source']
        self.other_data = other_event
        self.other_data_str = json.dumps(self.other_data)

    def get_info_list(self):
        return [self.time_int, self.time_elaps, self.event_type, self.source_id, self.source_type, self.other_data_str]


def get_source_desc(source):
    return 'id: %s, type: %s' % (source['id'], constant_converter.get_source_type(source['type']))

if __name__ == '__main__':
    event_log_str = '{"params":{"new_config":{"auto_detect":true}},"phase":0,"source":{"id":7,"type":0},"time":"87726889","type":27}'
    event_log_obj = json.loads(event_log_str)
    event = ChromeEvent(event_log_obj)
    print(event.get_info_list())