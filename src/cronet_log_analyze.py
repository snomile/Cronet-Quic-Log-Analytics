import os
import sys

from process import cronet_log_loader
from visualize import helper_data, helper_graph
from visualize import graph

if __name__ == '__main__':
    #check key directory exist
    abs_py_path = os.path.abspath(sys.argv[0])
    project_root = abs_py_path[:abs_py_path.index('/src/cronet_log_analyze.py')]
    cur_abs_path = os.path.abspath(os.curdir)
    key_paths = [project_root + '/resource/html_output',
                project_root + '/resource/data_original',
                project_root + '/resource/data_converted'
                ]
    for key_path in key_paths:
        if not os.path.exists(key_path):
            os.makedirs(key_path)


    # find usable input path
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "some_file_name2.json"
        #file_path = "netlog-2.json"
    paths = [file_path,
             cur_abs_path + '/' + file_path,
             project_root + '/resource/data_original/' + file_path]
    usable_input_path = None
    for usable_input_path in paths:
        if os.path.exists(usable_input_path):
           break


    # process and show graph
    if usable_input_path:
        print('find file on ', usable_input_path)
        (filepath, tempfilename) = os.path.split(usable_input_path)
        (filename_without_ext, extension) = os.path.splitext(tempfilename)

        #process data
        json_files = cronet_log_loader.process_chrome_log(usable_input_path, project_root + "/resource/data_converted/", filename_without_ext)

        #show graph
        for json_file in json_files:
            helper_data.init(json_file)
            json_file_name_without_ext = json_file[json_file.rfind('/')+1: -21]
            host_starttime = json_file_name_without_ext.replace(filename_without_ext+ '_','')
            helper_graph.init(project_root, json_file_name_without_ext,host_starttime)
            graph.show()
    else:
        print('file %s does not exist, exit now' % file_path)