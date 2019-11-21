import json
import os

import constant_converter
import visualize
from chrome_session import ChromeSession, ChromeEvent
from quic_session import QuicConnection


def fix_trunced_file(file_path):
    filesize = os.path.getsize(file_path)
    with open(file_path, 'r+') as load_f:
        # fix trunced file
        load_f.seek(filesize-2, 0)
        last_char = load_f.read(1)
        if ',' == last_char:
            print('file trunced, fixed by appending ]}')
            load_f.seek(filesize - 2, 0)
            load_f.write(']}')
        else:
            print('no need to fix')

def process_chrome_log(file_path):
    #get file info
    (filepath, tempfilename) = os.path.split(file_path)
    (filename, extension) = os.path.splitext(tempfilename)

    #load log data
    with open(file_path, 'r') as load_f:
        load_dict = json.load(load_f)
        constants = load_dict['constants']
        log_events = load_dict['events']
        print('load', len(log_events), 'events')

    #convert and save chrome event log
    constant_converter.init(constants)
    start_time = int(log_events[0]['time'])
    chrome_session = ChromeSession(start_time, "../data_converted/" + filename + '.csv')
    for log_event in log_events:
        c_event = ChromeEvent(log_event)
        chrome_session.add_event(c_event)
    chrome_session.save()

    #extract quic session log
    quic_session = QuicConnection(chrome_session.event_list, "../data_converted/" + filename)
    quic_session.save()


if __name__ == '__main__':
    file_path = "../data_original/quic-gh2ir.json"
    #file_path = "../data_original/quic-sa2ir_slow.json"
    fix_trunced_file(file_path)
    process_chrome_log(file_path)

    # visualize.init(file_path)
    # visualize.show()