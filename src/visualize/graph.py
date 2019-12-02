from visualize import graph_client_receive_send_data, helper_data, helper_graph
from visualize import graph_packet_ack_delay
from visualize import graph_packet_size_inflight

def show(show_all_packet_info,show_receive_send = True, show_ack_delay = True, show_size_inflight = True):
    if show_receive_send:
        graph_client_receive_send_data.show(show_all_packet_info)
    if show_ack_delay:
        graph_packet_ack_delay.show()
    if show_size_inflight:
        graph_packet_size_inflight.show()

if __name__ == '__main__':
    helper_graph.init('/Users/zhangliang/PycharmProjects/chrome_quic_log_analytics')
    helper_data.init("../resource/data_converted/netlog-2_quic_connection.json")
    #helper_data.init("../../resource/data_converted/quic-gh2ir_quic_connection.json")
    show()
