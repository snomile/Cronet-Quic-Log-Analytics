import csv
import json
import os
import time

import constant_converter


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

def get_source_desc(source):
    return 'id: %s, type: %s' % (source['id'], constant_converter.get_source_type(source['type']))


first_time = 0
def get_event_desc(event):
    global first_time
    try:
        #extract time
        time_int = int(event['time'])
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_int))
        if first_time == 0 :
            time_diff = 0
            first_time = time_int
        else:
            time_diff = time_int - first_time

        #extract event type
        event_type = constant_converter.get_event_type(event['type'])

        #extract other info
        del event['time']
        del event['type']
        other_info = json.dumps(event)

        return [time_str,time_diff,event_type,other_info]
    except BaseException as e:
        print(event)
        print(e)
        raise e

def process_chrome_log(file_path):
    #load log
    with open(file_path, 'r') as load_f:
        load_dict = json.load(load_f)

    constants = load_dict['constants']
    events = load_dict['events']
    print('load',len(events),'events')

    #init converter
    constant_converter.init(constants)

    #convert and save data
    (filepath, tempfilename) = os.path.split(file_path)
    (filename, extension) = os.path.splitext(tempfilename)
    with open("../data_converted/"+filename+'.csv','wt') as f:
        cw = csv.writer(f)
        for event in events:
            cw.writerow(get_event_desc(event))



if __name__ == '__main__':
    file_path = "../data_original/quic-gh2ir.json"
    #file_path = '/Volumes/Storage/临时/log.json'

    fix_trunced_file(file_path)
    process_chrome_log(file_path)

