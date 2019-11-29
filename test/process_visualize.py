import os

from process import chrome_log_loader
from visualize import prepare_data
from visualize import graph_bokhe

if __name__ == '__main__':
    file_path = "../data_original/quic-gh2ir.json"
    #file_path = "../data_original/netlog-1.json"

    (filepath, tempfilename) = os.path.split(file_path)
    (filename, extension) = os.path.splitext(tempfilename)

    #process data
    chrome_log_loader.process_chrome_log(file_path)

    #show graph
    prepare_data.init("../data_converted/" + filename + '_quic_connection.json')
    graph_bokhe.show_client_receive_send_data()