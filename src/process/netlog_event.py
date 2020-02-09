import json

from process import constant_converter


class NetlogEvent():
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
    event = NetlogEvent(event_log_obj)
    print(event.get_info_list())