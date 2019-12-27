import json
import os
import sys
import argparse
import time

from process import cronet_log_loader,cronet_session
from visualize import helper_data, helper_graph
from visualize import graph

def check_key_path(project_root,output_path):
    key_paths = [project_root + '/resource/html_output',
                 project_root + '/resource/data_original',
                 project_root + '/resource/data_converted',
                 output_path
                 ]
    for key_path in key_paths:
        if not os.path.exists(key_path):
            os.makedirs(key_path)

def find_usable_input_path(file_path):
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

def process_show(usable_input_path,args):
    print('find file on ', usable_input_path)
    (filepath, tempfilename) = os.path.split(usable_input_path)
    (filename_without_ext, extension) = os.path.splitext(tempfilename)

    # process data
    json_files = cronet_log_loader.process_chrome_log(usable_input_path, project_root, args.output_path,filename_without_ext)

    # show graph
    for json_file in json_files:
        helper_data.init(json_file)
        json_file_name_without_ext = json_file[json_file.rfind('/') + 1: -21]
        host_starttime = json_file_name_without_ext.replace(filename_without_ext + '_', '')
        helper_graph.init(args.output_path, filename_without_ext, host_starttime)
        graph.show(args.show_all_packet_info,args.show_receive_send, args.show_ack_delay, args.show_size_inflight)




def generate_event_session_result(output_path):
    files = os.listdir(output_path)
    event_session_dict = {}
    for file in files:
        if file.endswith('_general_info.json'):
            event_session_name = file[:file.index('_general_info.json')]
            event_session_files = [event_session_file for event_session_file in files if event_session_file.startswith(event_session_name)]
            event_session_dict[event_session_name]=event_session_files

    event_session_info_name = output_path + 'event_session_info.json'
    with open(event_session_info_name, "w") as f:
        json.dump(event_session_dict, f)

    print("generate event session info:", event_session_info_name)


if __name__ == '__main__':
    #extract args
    abs_program_path = os.path.abspath(sys.argv[0])
    project_root = abs_program_path[:abs_program_path.index('/src/cronet_log_analyze.py')]

    parser = argparse.ArgumentParser()
    parser.add_argument("--log_path", help="absloute path of the log file", default = 'some_file_name2.json')
    parser.add_argument("--output_path", help="absloute path of the output files", default= "%s/resource/data_converted/%s/" % (project_root, time.time()))
    parser.add_argument("--show_all_packet_info", help="show_all_packet_info", default=True)
    parser.add_argument("--show_receive_send", help="show_receive_send", default=True)
    parser.add_argument("--show_ack_delay", help="show_ack_delay", default=False)
    parser.add_argument("--show_size_inflight", help="show_size_inflight", default=False)
    parser.add_argument("--ignore", help="domain ignored", default='google.com;googleapis.com;doubleclick.net;google-analytics.com')

    args = parser.parse_args()
    cronet_session.IGNORE_DOMAIN_NAME_LIST = args.ignore.split(';')
    print(args)

    #process data
    check_key_path(project_root,args.output_path)
    usable_input_path = find_usable_input_path(args.log_path)
    if usable_input_path:
        process_show(usable_input_path,args)
        generate_event_session_result(args.output_path)
    else:
        print('file %s does not exist, exit now' % usable_input_path)
