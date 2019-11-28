#TODO:
# 1) packet on the fly in time secquence, with CFCW/SFCW size info overlay
# 2) ack distence in time and packet number（发现ack间距大，而CFCW和SFCW又没有变大的问题）
import json
import os

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

frame_dict = {}
packet_sent_dict = {}
packet_received_dict = {}
general_info = {}


def init(original_file_path):
    global frame_dict,packet_sent_dict,packet_received_dict,general_info
    (filepath, tempfilename) = os.path.split(original_file_path)
    (filename, extension) = os.path.splitext(tempfilename)
    with open('../data_converted/' + filename+ '_quic_connection.json', 'r') as load_f:
        load_dict = json.load(load_f)
        frame_dict = load_dict['frame_dict']
        packet_sent_dict = load_dict['packet_sent_dict']
        packet_received_dict = load_dict['packet_received_dict']
        general_info = load_dict['general_info']

    print('load general info: ', len(general_info))
    print('load packet_sent: ', len(packet_sent_dict))
    print('load packet_received: ', len(packet_received_dict))
    print('load stream_dict: ', len(load_dict['stream_dict']))
    print('load frame_dict: ', len(frame_dict))

def show():
    show_packet_ack_delay_all()
    show_server_cfcw_update_info()

def calculate_packet_ack_delay():
    packet_sent_time_sequence_list = []
    ack_delay_total_list = []
    ack_delay_server_list = []

    for packet in packet_sent_dict.values():
        packet_sent_time_sequence_list.append(int(packet['time']))
        ack_delay_total = int(packet['ack_delay'])
        ack_delay_total_list.append(ack_delay_total)
        ack_frame_id = packet['ack_by_frame']
        if ack_frame_id == 'N/A':
            if packet['info'][7][0][0] == 'ACK':
                ack_delay_server_list.append(0) # the last ack packet won't be acked, manually set the ack_delay_server to 0
            else:
                print('WARN: Possible error packet: ', packet['number'], ', which is not ACKed')
        else:
            ack_frame = frame_dict[ack_frame_id]
            ack_delay_server = round(float(ack_frame['delta_time_largest_observed_us'])/1000,3)
            ack_delay_server_list.append(ack_delay_server)

    return packet_sent_time_sequence_list,ack_delay_total_list


def calculate_packet_lost_timestamp():
    lost_packet_number_list = []
    lost_packet_sent_time_sequence_list = []
    lost_packet_sent_ack_delay_list = []

    #find all lost packet number
    for frame in frame_dict.values():
        if frame['frame_type'] == 'ACK' and frame['direction'] == 'receive' and len(frame['missing_packets'])>0:
            lost_packet_numbers = frame['missing_packets']  #TODO check the consistency with QUIC_SESSION_PACKET_LOST
            lost_packet_number_list.extend(lost_packet_numbers)

    for packet in packet_sent_dict.values():
        if packet['number'] in lost_packet_number_list:
            lost_packet_sent_time_sequence_list.append(int(packet['time']))
            ack_delay_total = int(packet['ack_delay'])
            lost_packet_sent_ack_delay_list.append(ack_delay_total)

    return lost_packet_sent_time_sequence_list,lost_packet_sent_ack_delay_list


def calculate_rtt():
    rtt_timestamp = []
    rtt_list = []
    for frame in frame_dict.values():
        if frame['frame_type'] == 'ACK' and frame['direction'] == 'receive':
            largest_observed_packet_number = frame['largest_observed']
            largest_observed_packet_ack_delay = packet_sent_dict[str(largest_observed_packet_number)]['ack_delay']
            ack_delay_server = round(float(frame['delta_time_largest_observed_us']) / 1000, 3)
            rtt = largest_observed_packet_ack_delay - ack_delay_server
            rtt_timestamp.append(int(packet_sent_dict[str(largest_observed_packet_number)]['time']))
            rtt_list.append(rtt)
    return rtt_timestamp,rtt_list

def calculate_packet_size_on_the_fly():
    #find all ack time and length
    ack_time_cfcw_dict = {}
    for frame in frame_dict.values():
        if frame['frame_type'] == 'ACK' and frame['direction'] == 'receive':
            ack_packet_number_list = frame['ack_packet_number_list']
            total_ack_size = 0
            for ack_packet_number in ack_packet_number_list:
                ack_packet = packet_sent_dict[str(ack_packet_number)]
                ack_packet_length = ack_packet['length']
                total_ack_size += ack_packet_length
            ack_time_cfcw_dict[frame['frame_id']] = (frame['time_elaps'],total_ack_size)
    #calculate packet size on the fly per send event, if the ack time between previous event time and current event time, then the on_the_fly_size should minus the ack_length
    packet_sent_list = list(packet_sent_dict.values())
    current_receiver_windows_offset = packet_sent_list[0]['length']
    on_the_fly_packet_size_list = [current_receiver_windows_offset/1024]
    packet_sent_time_sequence_list = [int(packet_sent_list[0]['time'])]
    for i in range(1, len(packet_sent_list)):
        previous_packet = packet_sent_list[i - 1]
        packet = packet_sent_list[i]
        packet_sent_time_sequence_list.append(int(packet['time']))
        current_receiver_windows_offset += packet['length']
        previous_sent_time = previous_packet['time']
        current_sent_time = packet['time']
        for frame_id, (ack_time, ack_length) in ack_time_cfcw_dict.items():
            if previous_sent_time < ack_time and current_sent_time >= ack_time:
                current_receiver_windows_offset -= ack_length
        on_the_fly_packet_size_list.append(current_receiver_windows_offset/1024)

    return packet_sent_time_sequence_list,on_the_fly_packet_size_list

def calculate_server_cfcw():
    #init by default server cfcw
    cfcw_timestamp = [0]
    cfcw_list = [general_info['Server_CFCW']/1024]

    #add server window_update info
    for frame in frame_dict.values():
        if frame['frame_type'] == 'WINDOW_UPDATE' and frame['direction'] == 'receive' and frame['stream_id'] == 0:
            byte_offset = frame['byte_offset']
            cfcw_list.append(byte_offset/1024)
            cfcw_timestamp.append(frame['time_elaps'])

    return cfcw_timestamp,cfcw_list

def calculate_client_cfcw():
    #init by default client cfcw
    cfcw_timestamp = [0]
    cfcw_list = [general_info['Client_CFCW']/1024]

    #add server window_update info
    for frame in frame_dict.values():
        if frame['frame_type'] == 'WINDOW_UPDATE' and frame['direction'] == 'send' and frame['stream_id'] == 0:
            byte_offset = frame['byte_offset']
            cfcw_list.append(byte_offset/1024)
            cfcw_timestamp.append(frame['time_elaps'])

    return cfcw_timestamp,cfcw_list

def calcualte_total_sent_size():
    total_sent_size_list = []
    total_sent_size = 0
    packet_sent_time_sequence_list = []
    for packet in packet_sent_dict.values():
        packet_sent_time_sequence_list.append(int(packet['time']))
        total_sent_size += packet['length']
        total_sent_size_list.append(total_sent_size/1024)
    return packet_sent_time_sequence_list,total_sent_size_list

def calcualte_total_received_size():
    total_received_size_list = []
    total_received_size = 0
    packet_sent_time_sequence_list = []
    for packet in packet_received_dict.values():
        packet_sent_time_sequence_list.append(int(packet['time']))
        total_received_size += packet['length']
        total_received_size_list.append(total_received_size/1024)
    return packet_sent_time_sequence_list,total_received_size_list

def calculate_client_block():
    block_timestamp = []
    block_stream_id_list = []
    for frame in frame_dict.values():
        if frame['frame_type'] == 'BLOCKED' and frame['direction'] == 'send':
            block_stream_id_list.append(frame['stream_id'])
            block_timestamp.append(frame['time_elaps'])
    return block_timestamp,block_stream_id_list

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
    cfcw_timestamp.append(packet_sent_time_sequence_list[-1])
    cfcw_list.append(cfcw_list[0])

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
    cfcw_timestamp.append(packet_receive_time_sequence_list[-1])
    cfcw_list.append(cfcw_list[-1])

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

if __name__ == '__main__':
    #init("../data_original/quic-gh2ir.json")
    init("../data_original/netlog.json")

    show_packet_size_on_the_fly()
    show_packet_ack_delay_all()
    show_server_cfcw_update_info()
    show_client_cfcw_update_info()
