from visualize import graph_client_receive_send_data, helper_data
from visualize import graph_packet_ack_delay
from visualize import graph_packet_size_inflight

def show():
    helper_data.init("../resource/data_converted/netlog-2_quic_connection.json")
    #init("../data_converted/quic-gh2ir_quic_connection.json")

    graph_client_receive_send_data.show()
    graph_packet_ack_delay.show()
    graph_packet_size_inflight.show()

if __name__ == '__main__':
    show()
