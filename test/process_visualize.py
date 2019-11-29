import os

from process import cronet_log_loader
from visualize import helper_data
from visualize import graph

if __name__ == '__main__':
    file_path = "../resource/data_original/quic-gh2ir.json"
    #file_path = "../resource/data_original/netlog-2.json"

    (filepath, tempfilename) = os.path.split(file_path)
    (filename, extension) = os.path.splitext(tempfilename)

    #process data
    cronet_log_loader.process_chrome_log(file_path)

    #show graph
    helper_data.init("../resource/data_converted/" + filename + '_quic_connection.json')
    graph.show()