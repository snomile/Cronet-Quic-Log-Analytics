import json

from bokeh.models import ColumnDataSource

frame_dict = {}
packet_sent_dict = {}
packet_received_dict = {}
general_info = {}
key_time = {}


def init(file_path):
    global frame_dict,packet_sent_dict,packet_received_dict,general_info,key_time
    with open(file_path, 'r') as load_f:
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

    #add last point
    last_receive_packet = list(packet_received_dict.values())[-1]
    last_receive_time = int(last_receive_packet['time'])
    cfcw_timestamp.append(last_receive_time)
    cfcw_list.append(cfcw_list[-1])

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

    #add last point
    last_send_packet = list(packet_sent_dict.values())[-1]
    last_send_time = int(last_send_packet['time'])
    cfcw_timestamp.append(last_send_time)
    cfcw_list.append(cfcw_list[-1])

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

def calculate_client_block_connection_level():
    block_timestamp = []
    for frame in frame_dict.values():
        if frame['frame_type'] == 'BLOCKED' and frame['direction'] == 'send' and frame['stream_id'] == 0:
            block_timestamp.append(frame['time_elaps'])
    return block_timestamp

def get_dns_source():
    source = ColumnDataSource(data={
        'x': [general_info['DNS_begin_time'], general_info['DNS_end_time']],
        'y': [-1, -1],
        'name': ['dns begin', 'dns end']
    })
    return source

def get_packet_send_source():
    packet_sent_time_sequence_list, total_sent_size_list = calcualte_total_sent_size()
    source = ColumnDataSource(data={
        'x': packet_sent_time_sequence_list,
        'y': total_sent_size_list,
    })
    return source

def get_packet_receive_source():
    packet_receive_time_sequence_list, total_receive_size_list = calcualte_total_received_size()
    source = ColumnDataSource(data={
        'x': packet_receive_time_sequence_list,
        'y': total_receive_size_list,
    })
    return source

def get_client_cfcw_source():
    client_cfcw_timestamp, client_cfcw_list = calculate_client_cfcw()
    source = ColumnDataSource(data={
        'x': client_cfcw_timestamp,
        'y': client_cfcw_list,
    })
    return source

def get_server_cfcw_source():
    server_cfcw_timestamp, server_cfcw_list = calculate_server_cfcw()
    source = ColumnDataSource(data={
        'x': server_cfcw_timestamp,
        'y': server_cfcw_list,
    })
    return source

def get_client_block_connection_level_source():
    client_block_timestamp, client_block_stream_id_list = calculate_client_block()
    color_list = []
    for client_block_stream_id in client_block_stream_id_list:
        if client_block_stream_id ==0:
            color_list.append('red')
        else:
            color_list.append('yellow')

    source = ColumnDataSource(data={
        'x': client_block_timestamp,
        'y': [-1] * len(client_block_timestamp),
        'stream_id': client_block_stream_id_list,
        'color': color_list
    })
    return source