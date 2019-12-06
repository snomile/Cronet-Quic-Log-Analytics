import json
import os

from process import constant_converter
from process.cronet_session import CronetSession, CronetEvent


def fix_trunced_file(file_path):
    with open(file_path, 'rb+') as load_f:
        # fix trunced file
        load_f.seek(-5, 2)
        last_char = str(load_f.read(5), encoding="utf-8").strip('\r\n')
        if last_char.endswith('],'):
            new_last_char = last_char[: last_char.index('],')] + ']}   '
            print('file trunced, fixed by appending }')
            load_f.seek(-5, 2)
            load_f.write(bytes(new_last_char, encoding="utf8"))
        elif last_char.endswith('},'):
            new_last_char = last_char[: last_char.index('},')] + '}]}   '
            print('file trunced, fixed by appending }]}')
            load_f.seek(-5, 2)
            load_f.write(bytes(new_last_char, encoding="utf8"))
        else:
            print('no need to fix')

def process_chrome_log(fullpath, data_original_path, data_converted_path, filename_without_ext):
    #fix file
    fix_trunced_file(fullpath)

    #load log data
    with open(fullpath, 'r') as load_f:
        load_dict = json.load(load_f)

    if 'constants' in load_dict.keys():
        constants = load_dict['constants']
    else:
        with open(data_original_path + '/constants.json', 'r') as load_f:
            constants = json.load(load_f)['constants']
    log_events = load_dict['events']
    print('load', len(log_events), 'events')

    #convert and save chrome event log
    constant_converter.init(constants)
    start_time = int(log_events[0]['time'])
    cronet_session = CronetSession(start_time, data_converted_path , filename_without_ext)
    for log_event in log_events:
        c_event = CronetEvent(log_event)
        cronet_session.add_event(c_event)

    cronet_session.save()
    json_files = cronet_session.create_quic_session()
    print('log file process finished')

    return json_files


if __name__ == '__main__':
    file_path = "../resource/data_original/netlog-2.json"
    process_chrome_log(file_path)
