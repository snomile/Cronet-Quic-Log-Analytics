import os
import sys

from process import cronet_log_loader
from visualize import helper_data, helper_graph
from visualize import graph

if __name__ == '__main__':
    abs_py_path = os.path.abspath(sys.argv[0])
    project_root = abs_py_path[:abs_py_path.index('/src/cronet_log_analyze.py')]
    cur_abs_path = os.path.abspath(os.curdir)

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "some_file_name2.json"
        #file_path = "netlog-2.json"

    paths = [file_path,
             cur_abs_path + '/' + file_path,
             project_root + '/resource/data_original/' + file_path]
    path = None
    for path in paths:
        if os.path.exists(path):
           break

    if path:
        print('find file on ', path)
        (filepath, tempfilename) = os.path.split(path)
        (filename, extension) = os.path.splitext(tempfilename)

        #process data
        cronet_log_loader.process_chrome_log(path, project_root, filename)

        #show graph
        helper_data.init(project_root + "/resource/data_converted/" + filename + '_quic_connection.json')
        helper_graph.init(project_root,filename)
        graph.show()
    else:
        print('file %s does not exist, exit now' % file_path)