import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from visualize.prepare_data import *


def show_packet_ack_delay_all():
    packet_sent_time_sequence_list,ack_delay_total_list = calculate_packet_ack_delay()
    lost_packet_sent_time_sequence_list, lost_packet_sent_ack_delay_list = calculate_packet_lost_timestamp()
    rtt_timestamp, rtt_list = calculate_rtt()

    plt.scatter(packet_sent_time_sequence_list, ack_delay_total_list, color='g', marker='.',label='Packet ack delay')
    plt.scatter(lost_packet_sent_time_sequence_list, lost_packet_sent_ack_delay_list, color='r', marker='*', label='Packet LOST')
    plt.scatter(rtt_timestamp, rtt_list, color='b',marker='_', label='RTT')
    #plt.ylim((80, 200))
    plt.xlabel('Packet Sent Time Offset (ms)')
    plt.ylabel('Latency (ms)')
    plt.title("Packet ACK Delay")
    plt.legend()
    plt.show()

def show_packet_size_on_the_fly():
    packet_sent_time_sequence_list,on_the_fly_packet_size_list = calculate_packet_size_on_the_fly()
    plt.plot(packet_sent_time_sequence_list, on_the_fly_packet_size_list)
    plt.xlabel('Packet Sent Time Offset (ms)')
    plt.ylabel('Packet Size (KB)')
    plt.title("Inflight Packet Size ")
    plt.legend()
    plt.grid(True)
    plt.show()


def show_server_cfcw_update_info():
    cfcw_timestamp, cfcw_list = calculate_server_cfcw()
    packet_sent_time_sequence_list,total_sent_size_list = calcualte_total_sent_size()
    block_timestamp, block_stream_id_list = calculate_client_block()

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(cfcw_timestamp, cfcw_list, label='Server CFCW Offset')
    ax1.plot(packet_sent_time_sequence_list, total_sent_size_list, label='Total Sent Size')
    ax1.set_ylabel('Client Packet Sent (KB)')
    ax1.set_title('Server CFCW and Client Sent Size')
    ax1.legend()

    ax2 = ax1.twinx()  # this is the important function
    ax2.scatter(block_timestamp, block_stream_id_list, marker='*')
    ax2.set_ylabel('Blocked Stream ID')
    ax2.legend()

    plt.legend()
    plt.grid(True)
    plt.show()

def show_client_cfcw_update_info():
    cfcw_timestamp, cfcw_list = calculate_client_cfcw()
    packet_receive_time_sequence_list,total_receive_size_list = calcualte_total_received_size()
    #block_timestamp, block_stream_id_list = calculate_server_block()

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    #ax1.plot(cfcw_timestamp, cfcw_list, label='Client CFCW Offset')
    ax1.plot(packet_receive_time_sequence_list, total_receive_size_list, label='Total Received Size')
    ax1.set_ylabel('Packet Received (KB)')
    ax1.set_title('Client CFCW and Received Size')
    ax1.legend()

    ax2 = ax1.twinx()  # this is the important function
    #ax2.scatter(block_timestamp, block_stream_id_list, marker='*')
    ax2.set_ylabel('Blocked Stream ID')
    ax2.legend()

    plt.legend()
    plt.grid(True)
    plt.show()

#show timestamp for client init, dns resolve, handshaking, http header send, first http response receive
# def show_connection_start_stage():
#
#
#     plt.scatter(packet_sent_time_sequence_list, ack_delay_total_list, color='g', marker='.',label='Packet ack delay')
#     plt.scatter(lost_packet_sent_time_sequence_list, lost_packet_sent_ack_delay_list, color='r', marker='*', label='Packet LOST')
#     plt.scatter(rtt_timestamp, rtt_list, color='b',marker='_', label='RTT')
#     #plt.ylim((80, 200))
#     plt.xlabel('Packet Sent Time Offset (ms)')
#     plt.ylabel('Latency (ms)')
#     plt.title("Packet ACK Delay")
#     plt.legend()
#     plt.show()
#
#
#     x = key_time.values()
#     y =
#
#     for phase_name, time_elaps in key_time:
#
#     pass


if __name__ == '__main__':
    #init("../data_converted/netlog-1_quic_connection.json")
    init("../data_converted/quic-gh2ir_quic_connection.json")

    show_packet_size_on_the_fly()
    show_packet_ack_delay_all()
    show_server_cfcw_update_info()
    show_client_cfcw_update_info()
