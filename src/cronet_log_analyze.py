import os
import sys

from process import cronet_log_loader,cronet_session
from visualize import helper_data, helper_graph
from visualize import graph

file_path = "netlog-1575103171.json"
#file_path = "netlog-2.json"

show_all_packet_info = True
show_receive_send = True
show_ack_delay = False
show_size_inflight = False
ignore_list = [] # ['google.com','googleapis.com','doubleclick.net','google-analytics.com']


def check_key_path(project_root):
    key_paths = [project_root + '/resource/html_output',
                 project_root + '/resource/data_original',
                 project_root + '/resource/data_converted'
                 ]
    for key_path in key_paths:
        if not os.path.exists(key_path):
            os.makedirs(key_path)


def find_usable_input_path():
    global file_path
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    cur_abs_path = os.path.abspath(os.curdir)
    paths = [file_path,
             cur_abs_path + '/' + file_path,
             project_root + '/resource/data_original/' + file_path]
    usable_input_path = None
    for usable_input_path in paths:
        if os.path.exists(usable_input_path):
            break
    return usable_input_path

def str_to_bool(str):
    return True if str.lower() == 'true' else False

def process_show(usable_input_path, argv):
    global show_all_packet_info,show_receive_send,show_ack_delay,show_size_inflight,ignore_list
    if len(argv) >= 6:
        show_all_packet_info = str_to_bool(argv[2])
        show_receive_send = str_to_bool(argv[3])
        show_ack_delay = str_to_bool(argv[4])
        show_size_inflight = str_to_bool(argv[5])

    for i in range(6, len(argv)):
        ignore_list.append(argv[i])
    cronet_session.IGNORE_DOMAIN_NAME_LIST = ignore_list

    print('show_all_packet_info: ',show_all_packet_info)
    print('show_receive_send: ', show_receive_send)
    print('show_ack_delay: ', show_ack_delay)
    print('show_size_inflight: ', show_size_inflight)
    print('ignore_list: ',ignore_list)

    if usable_input_path:
        print('find file on ', usable_input_path)
        (filepath, tempfilename) = os.path.split(usable_input_path)
        (filename_without_ext, extension) = os.path.splitext(tempfilename)

        # process data
        json_files = cronet_log_loader.process_chrome_log(usable_input_path, project_root + "/resource/data_converted/",
                                                          filename_without_ext)

        # show graph
        for json_file in json_files:
            helper_data.init(json_file)
            json_file_name_without_ext = json_file[json_file.rfind('/') + 1: -21]
            host_starttime = json_file_name_without_ext.replace(filename_without_ext + '_', '')
            helper_graph.init(project_root, filename_without_ext, host_starttime)
            graph.show(show_all_packet_info,show_receive_send, show_ack_delay, show_size_inflight)
    else:
        print('file %s does not exist, exit now' % file_path)


def show_help():
    print('usage: python3 cronet_log_analyze.py $log_file_path $show_all_packet_info $show_receive_send $show_ack_delay $show_size_inflight $ignore_domain_list')
    print(
        'eg: python3 cronet_log_analyze.py /home/me/netlog-2.json False True False False www.google.com googleapi.com doubleclick.net')
    print('or, simply use: python3 cronet_log_analyze.py /home/me/netlog-2.json, other parameters will take default value')
    os._exit(0)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', 'help']:
        show_help()

    abs_program_path = os.path.abspath(sys.argv[0])
    project_root = abs_program_path[:abs_program_path.index('/src/cronet_log_analyze.py')]
    check_key_path(project_root)
    usable_input_path = find_usable_input_path()
    process_show(usable_input_path,sys.argv)