import csv
import json
import os
import time

import constant_converter
import quic_session

ingore_event_type_list = [
    'QUIC_SESSION_PACKET_AUTHENTICATED'
]

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
        other_event = event.copy()
        del other_event['time']
        del other_event['type']
        other_info = json.dumps(other_event)

        return [time_str,time_diff,event_type,other_info]
    except BaseException as e:
        print(event)
        print(e)
        raise e

def process_chrome_log(file_path):
    #get file info
    (filepath, tempfilename) = os.path.split(file_path)
    (filename, extension) = os.path.splitext(tempfilename)

    #load log
    with open(file_path, 'r') as load_f:
        load_dict = json.load(load_f)

    constants = load_dict['constants']
    events = load_dict['events']
    print('load',len(events),'events')

    #convert and save all data
    constant_converter.init(constants)
    with open("../data_converted/"+filename+'.csv','wt') as f:
        cw = csv.writer(f)
        for event in events:
            cw.writerow(get_event_desc(event))

    #TODO clean illgate peer_address data
    #extract quic session
    with open("../data_converted/"+filename+'_quic_session.csv','wt') as f:
        cw = csv.writer(f)

        i = 0
        length = len(events)
        print('events to process: ',length)
        while i < length:
            event = events[i]
            event_info_list = get_event_desc(event)
            event_type = event_info_list[2]
            if event_type not in ingore_event_type_list:
                if 'QUIC' in event_type:
                    if event_type == 'QUIC_SESSION_PACKET_RECEIVED':
                        next_event = events[i+1]
                        next_event_info_list = get_event_desc(next_event)
                        next_event_type = next_event_info_list[2]
                        if next_event_type != 'QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED':
                            raise BaseException('packet received but no QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED event follows')
                        else:
                            combined_event_obj = quic_session.packet_received(event, next_event)
                            combined_event_info = event_info_list[:3]
                            combined_event_info.append(combined_event_obj.to_string())
                            cw.writerow(combined_event_info)
                            i += 1
                    else:
                        cw.writerow(get_event_desc(event))
                print('event processed: ',i)
            i += 1



if __name__ == '__main__':
    file_path = "../data_original/quic-gh2ir.json"
    #file_path = '/Volumes/Storage/临时/log.json'

    fix_trunced_file(file_path)
    process_chrome_log(file_path)

