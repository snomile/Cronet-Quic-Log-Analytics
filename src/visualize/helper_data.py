import json
from sklearn import preprocessing

from bokeh.models import ColumnDataSource

frame_dict = {}
stream_dict = {}
packet_sent_dict = {}
packet_received_dict = {}
general_info = {}
key_time = {}
chlo_dict = {}
shlo_dict = {}


def init(file_path):
    global frame_dict,packet_sent_dict,packet_received_dict,general_info,key_time,stream_dict,chlo_dict,shlo_dict
    with open(file_path, 'r') as load_f:
        load_dict = json.load(load_f)
        frame_dict = load_dict['frame_dict']
        packet_sent_dict = load_dict['packet_sent_dict']
        packet_received_dict = load_dict['packet_received_dict']
        general_info = load_dict['general_info']
        stream_dict = load_dict['stream_dict']

    print('load general info: ', len(general_info))
    print('load packet_sent: ', len(packet_sent_dict))
    print('load packet_received: ', len(packet_received_dict))
    print('load stream_dict: ', len(stream_dict))
    print('load frame_dict: ', len(frame_dict))

    #init CHLO and SHLO
    handshake_frame_ids = stream_dict['1']
    chlo_index = 1
    shlo_index = 1
    for frame_id in handshake_frame_ids:
        frame = frame_dict[frame_id]
        packet_number = frame['packet_number']
        if frame['direction'] == 'send':
            packet = packet_sent_dict[str(packet_number)]
            if packet['is_chlo']:
                handshake_type = 'CHLO' + str(chlo_index)
                chlo_dict[packet_number] = (handshake_type, frame['frame_info_str'])
                chlo_index += 1
        else:
            packet = packet_received_dict[str(packet_number)]
            if packet['is_shlo']:
                handshake_type = 'SHLO' + str(shlo_index)
                shlo_dict[packet_number] = (handshake_type, frame['info_list'])
                shlo_index += 1


def calculate_packet_ack_delay():
    packet_sent_time_sequence_list = []
    ack_delay_total_list = []
    ack_delay_server_list = []

    for packet in packet_sent_dict.values():
        packet_sent_time_sequence_list.append(int(packet['time']))
        ack_delay_total = int(packet['ack_delay'])
        ack_delay_total_list.append(ack_delay_total)
        ack_delay_server_list.append(packet['ack_delay_server'])

    return packet_sent_time_sequence_list,ack_delay_total_list,ack_delay_server_list


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
        'x': [general_info['dns_begin_time'], general_info['dns_end_time']],
        'y': [-1, -1],
        'name': ['dns begin', 'dns end']
    })
    return source

def get_packet_send_source(show_all_packet_info):
    total_sent_size = 0

    #for all packet
    all_packet_sent_time_sequence_list = []
    all_total_sent_size_list = []

    #for normal packet
    packet_sent_time_sequence_list = []
    packet_sent_time_readable_sequence_list = []
    total_sent_size_list = []
    packet_numbers = []
    ack_delay_total_list = []
    ack_delay_server_list = []
    colors = []
    tags = []
    infos = []

    #for chlo packet
    chlo_packet_sent_time_sequence_list = []
    chlo_packet_sent_time_readable_sequence_list = []
    chlo_total_sent_size_list = []
    chlo_packet_numbers = []
    chlo_ack_delay_total_list = []
    chlo_ack_delay_server_list = []
    chlo_colors = []
    chlo_tags = []
    chlo_infos = []

    for packet in packet_sent_dict.values():
        packet_sent_time = int(packet['time'])
        packet_sent_time_readable = packet['time_h']
        total_sent_size += packet['length']
        current_total_sent_size = total_sent_size / 1024
        ack_delay_total = int(packet['ack_delay'])
        ack_delay_server = int(packet['ack_delay_server'])

        all_packet_sent_time_sequence_list.append(packet_sent_time)
        all_total_sent_size_list.append(current_total_sent_size)

        if packet['number'] in chlo_dict.keys():
            chlo_packet_sent_time_sequence_list.append(packet_sent_time)
            chlo_packet_sent_time_readable_sequence_list.append(packet_sent_time_readable)
            chlo_total_sent_size_list.append(current_total_sent_size)
            chlo_packet_numbers.append(packet['number'])
            chlo_ack_delay_total_list.append(ack_delay_total)
            chlo_ack_delay_server_list.append(ack_delay_server)
            chlo_colors.append('yellow')
            chlo_tags.append(chlo_dict[packet['number']][0])
            chlo_infos.append(packet['info_str'])
        else:
            packet_sent_time_sequence_list.append(packet_sent_time)
            packet_sent_time_readable_sequence_list.append(packet_sent_time_readable)
            total_sent_size_list.append(current_total_sent_size)
            packet_numbers.append(packet['number'])
            ack_delay_total_list.append(ack_delay_total)
            ack_delay_server_list.append(ack_delay_server)

            if packet['is_lost'] :
                colors.append('red')
                tags.append('LOST')
                infos.append(packet['info_str'])
            elif packet['transmission_type'] != 'NOT_RETRANSMISSION':   #tag retramission type, only normal packet have variety of retramission type, all CHLO packet's retramission type is 'NOT_RETRANSMISSION', so no need to process
                colors.append('hotpink')
                tags.append(packet['transmission_type'])
                infos.append(packet['info_str'])
            else:
                colors.append('navy')
                tags.append('')
                if show_all_packet_info:
                    infos.append(packet['info_str'])
                else:
                    infos.append('')


    packet_send_line_source = ColumnDataSource(data={
        'x': all_packet_sent_time_sequence_list,
        'y': all_total_sent_size_list
    })

    packet_send_source = ColumnDataSource(data={
        'x': packet_sent_time_sequence_list,
        'y': total_sent_size_list,
        'time_h': packet_sent_time_readable_sequence_list,
        'number': packet_numbers,
        'ack_delay': ack_delay_total_list,
        'size': [] if len(ack_delay_total_list) == 0 else preprocessing.minmax_scale(ack_delay_total_list,feature_range=(5, 15)),
        'color': colors,
        'info': infos,
        'tag': tags
    })

    packet_send_chlo_source = ColumnDataSource(data={
        'x': chlo_packet_sent_time_sequence_list,
        'y': chlo_total_sent_size_list,
        'time_h': chlo_packet_sent_time_readable_sequence_list,
        'number': chlo_packet_numbers,
        'ack_delay': chlo_ack_delay_total_list,
        'size': [10] * len(chlo_packet_sent_time_sequence_list),
        'color': chlo_colors,
        'info' : chlo_infos,
        'tag': chlo_tags
    })

    return packet_send_line_source, packet_send_source, packet_send_chlo_source

def get_packet_receive_source(show_all_packet_info):
    current_total_received_size = 0

    #for all packet
    all_packet_receive_time_sequence_list = []
    all_total_received_size_list = []

    #for shlo packet
    shlo_packet_receive_time_sequence_list = []
    shlo_packet_receive_time_readable_sequence_list = []
    shlo_total_received_size_list = []
    shlo_packet_numer_list = []
    shlo_tags = []
    shlo_infos = []
    shlo_colors = []

    #for normal packet
    packet_receive_time_sequence_list = []
    packet_receive_time_readable_sequence_list = []
    total_received_size_list = []
    packet_numer_list = []
    tags = []
    infos = []
    colors = []
    for packet in packet_received_dict.values():
        current_total_received_size += packet['length']
        current_total_received_size_KB = current_total_received_size/1024

        all_packet_receive_time_sequence_list.append(int(packet['time']))
        all_total_received_size_list.append(current_total_received_size_KB)

        if packet['number'] in shlo_dict.keys():
            shlo_packet_receive_time_sequence_list.append(int(packet['time']))
            shlo_packet_receive_time_readable_sequence_list.append(packet['time_h'])
            shlo_total_received_size_list.append(current_total_received_size_KB)
            shlo_packet_numer_list.append(packet['number'])
            shlo_tags.append(shlo_dict[packet['number']][0])
            shlo_infos.append(packet['info_str'])
            shlo_colors.append('yellow')
        else:
            packet_receive_time_sequence_list.append(int(packet['time']))
            packet_receive_time_readable_sequence_list.append(packet['time_h'])
            total_received_size_list.append(current_total_received_size_KB)
            packet_numer_list.append(packet['number'])
            tags.append('')
            if show_all_packet_info:
                infos.append(packet['info_str'])
            else:
                infos.append('')
            colors.append('green')

    packet_receive_line_source = ColumnDataSource(data={
        'x': all_packet_receive_time_sequence_list,
        'y': all_total_received_size_list
    })

    packet_receive_source = ColumnDataSource(data={
        'x': packet_receive_time_sequence_list,
        'y': total_received_size_list,
        'time_h': packet_receive_time_readable_sequence_list,
        'number': packet_numer_list,
        'ack_delay': [''] * len(packet_receive_time_sequence_list),
        'size': [7] * len(packet_receive_time_sequence_list),
        'color': colors,
        'info' : infos,
        'tag': tags
    })

    packet_receive_shlo_source = ColumnDataSource(data={
        'x': shlo_packet_receive_time_sequence_list,
        'y': shlo_total_received_size_list,
        'time_h': shlo_packet_receive_time_readable_sequence_list,
        'number': shlo_packet_numer_list,
        'ack_delay': [''] * len(shlo_packet_receive_time_sequence_list),
        'size': [10] * len(shlo_packet_receive_time_sequence_list),
        'color': shlo_colors,
        'info' : shlo_infos,
        'tag': shlo_tags
    })

    return packet_receive_line_source, packet_receive_source, packet_receive_shlo_source


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


def get_packet_size_inflight():
    packet_sent_time_sequence_list, on_the_fly_packet_size_list = calculate_packet_size_on_the_fly()

    source = ColumnDataSource(data={
        'x': packet_sent_time_sequence_list,
        'y': on_the_fly_packet_size_list,
    })
    return source

def get_client_send_connection_close_source():
    connection_close_time_list = []
    infos = []
    actions = []

    for frame in frame_dict.values():
        if frame['frame_type'] == 'CONNECTION_CLOSE' and frame['direction'] == 'send':
            time = frame['time_elaps']
            connection_close_time_list.append(time)
            actions.append('Client_SEND_CONNECTION_CLOSE')
            infos.append('quic error: ' + frame['quic_error'])

    source = ColumnDataSource(data={
        'x': connection_close_time_list,
        'y': [-1] * len(connection_close_time_list),
        'name': actions ,
        'info': infos
    })
    return source