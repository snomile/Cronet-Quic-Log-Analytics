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

def check_valid():
    if general_info['session_type'] == 'client' and len(packet_sent_dict) == 0:
        return False
    else:
        return True


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
    on_the_fly_packet_size_list = []
    packet_sent_time_sequence_list = []

    if len(packet_sent_list)>0:
        current_receiver_windows_offset = packet_sent_list[0]['length']
        on_the_fly_packet_size_list.append(current_receiver_windows_offset/1024)
        packet_sent_time_sequence_list.append(int(packet_sent_list[0]['time']))
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

def get_ack_size_source():
    ack_receive_time_sequence_list = []
    total_acked_size_list = []
    total_ack_size = 0
    for frame in frame_dict.values():
        if frame['frame_type'] == 'ACK' and frame['direction'] == 'receive':
            ack_packet_number_list = frame['ack_packet_number_list']
            for ack_packet_number in ack_packet_number_list:
                ack_packet = packet_sent_dict[str(ack_packet_number)]
                ack_packet_length = ack_packet['length']
                total_ack_size += round(ack_packet_length/1024.0,2)
            total_acked_size_list.append(total_ack_size)
            ack_receive_time_sequence_list.append(frame['time_elaps'])

    ack_size_source = ColumnDataSource(data={
        'x': ack_receive_time_sequence_list,
        'y': total_acked_size_list,
    })
    return ack_size_source




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
    if general_info['dns_begin_time'] != general_info['dns_duration']:
        source = ColumnDataSource(data={
            'x': [general_info['dns_begin_time'], general_info['dns_duration']],
            'y': [-1, -1],
            'name': ['dns begin', 'dns end']
        })
    else:
        source = ColumnDataSource(data={
            'x': [],
            'y': [],
            'name': []
        })
    return source

def get_handshake_source():
    #chlo
    chlo_packet_sent_time_sequence_list = []
    chlo_packet_sent_time_readable_sequence_list = []
    chlo_packet_number_list = []
    chlo_ack_delay_total_list = []
    chlo_ack_delay_server_list = []
    chlo_colors = []
    chlo_tags = []
    chlo_infos = []

    #shlo
    shlo_packet_receive_time_sequence_list = []
    shlo_packet_receive_time_readable_sequence_list = []
    shlo_packet_numer_list = []
    shlo_ack_delay_total_list = []
    shlo_ack_delay_server_list = []
    shlo_colors = []
    shlo_tags = []
    shlo_infos = []


    #init CHLO and SHLO
    if '1' in stream_dict.keys():
        handshake_frame_ids = stream_dict['1']
        chlo_index = 0
        shlo_index = 0
        for frame_id in handshake_frame_ids:
            frame = frame_dict[frame_id]
            packet_number = frame['packet_number']
            if frame['direction'] == 'send':
                packet = packet_sent_dict[str(packet_number)]
            else:
                packet = packet_received_dict[str(packet_number)]
            packet_sent_time = int(packet['time'])
            packet_sent_time_readable = packet['time_h']

            if packet['direction'] == 'send':
                ack_delay_total = int(packet['ack_delay'])
                ack_delay_server = int(packet['ack_delay_server'])
            else:
                ack_delay_total = 0
                ack_delay_server = 0

            if packet['is_chlo']:
                chlo_index += 1
                chlo_packet_sent_time_sequence_list.append(packet_sent_time)
                chlo_packet_sent_time_readable_sequence_list.append(packet_sent_time_readable)
                chlo_packet_number_list.append(packet['number'])
                chlo_ack_delay_total_list.append(ack_delay_total)
                chlo_ack_delay_server_list.append(ack_delay_server)
                chlo_colors.append('yellow')
                chlo_tags.append('CHLO' + str(chlo_index))
                chlo_infos.append(packet['info_str'])
            elif packet['is_shlo']:
                shlo_index += 1
                shlo_packet_receive_time_sequence_list.append(int(packet['time']))
                shlo_packet_receive_time_readable_sequence_list.append(packet['time_h'])
                shlo_packet_numer_list.append(packet['number'])
                shlo_ack_delay_total_list.append(ack_delay_total)
                shlo_ack_delay_server_list.append(ack_delay_server)
                shlo_colors.append('yellow')
                shlo_tags.append('SHLO' + str(shlo_index))
                shlo_infos.append(packet['info_str'])

    chlo_source = ColumnDataSource(data={
        'x': chlo_packet_sent_time_sequence_list,
        'y': [-1] * len(chlo_packet_sent_time_sequence_list),
        'time_h': chlo_packet_sent_time_readable_sequence_list,
        'number': chlo_packet_number_list,
        'ack_delay': chlo_ack_delay_total_list,
        'size': [10] * len(chlo_packet_sent_time_sequence_list),
        'color': chlo_colors,
        'info': chlo_infos,
        'tag': chlo_tags
    })

    shlo_source = ColumnDataSource(data={
        'x': shlo_packet_receive_time_sequence_list,
        'y': [-1] * len(chlo_packet_sent_time_sequence_list),
        'time_h': shlo_packet_receive_time_readable_sequence_list,
        'number': shlo_packet_numer_list,
        'ack_delay': [''] * len(shlo_packet_receive_time_sequence_list),
        'size': [10] * len(shlo_packet_receive_time_sequence_list),
        'color': shlo_colors,
        'info' : shlo_infos,
        'tag': shlo_tags
    })

    return chlo_source, shlo_source



def get_packet_send_source(show_all_packet_info):
    total_sent_size = 0

    #for all packet  #TODO remove this
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

    for packet in packet_sent_dict.values():
        packet_sent_time = int(packet['time'])
        packet_sent_time_readable = packet['time_h']
        total_sent_size += packet['length']
        current_total_sent_size = round(total_sent_size / 1024.0,2)
        ack_delay_total = int(packet['ack_delay'])
        ack_delay_server = int(packet['ack_delay_server'])

        all_packet_sent_time_sequence_list.append(packet_sent_time)
        all_total_sent_size_list.append(current_total_sent_size)

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

    return packet_send_line_source, packet_send_source

def get_packet_receive_source(show_all_packet_info):
    current_total_received_size = 0

    #for all packet
    all_packet_receive_time_sequence_list = []
    all_total_received_size_list = []

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

    return packet_receive_line_source, packet_receive_source


def get_peer_cfcw_source():
    # init by default peer cfcw
    cfcw_timestamp = [0]
    if general_info['session_type'] == 'client':
        cfcw_list = [general_info['client_cfcw'] / 1024]
        for frame in frame_dict.values():
            if frame['frame_type'] == 'WINDOW_UPDATE' and frame['direction'] == 'send' and frame['stream_id'] == 0:
                byte_offset = frame['byte_offset']
                cfcw_list.append(byte_offset / 1024)
                cfcw_timestamp.append(frame['time_elaps'])
    else:
        cfcw_list = [general_info['server_cfcw'] / 1024]
        for frame in frame_dict.values():
            if frame['frame_type'] == 'WINDOW_UPDATE' and frame['direction'] == 'receive' and frame[
                'stream_id'] == 0:
                byte_offset = frame['byte_offset']
                cfcw_list.append(byte_offset / 1024)
                cfcw_timestamp.append(frame['time_elaps'])

    # add last point
    last_send_packet = list(packet_sent_dict.values())[-1]
    last_send_time = int(last_send_packet['time'])
    cfcw_timestamp.append(last_send_time)
    cfcw_list.append(cfcw_list[-1])

    source = ColumnDataSource(data={
        'x': cfcw_timestamp,
        'y': cfcw_list,
    })
    return source

def get_server_cfcw_source():
    #init by default server cfcw
    cfcw_timestamp = [0]
    cfcw_list = [general_info['server_cfcw']/1024]

    if len(packet_received_dict) > 0:
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

    source = ColumnDataSource(data={
        'x': cfcw_timestamp,
        'y': cfcw_list,
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

def get_connection_close_source():
    connection_close_time_list = []
    infos = []
    actions = []

    for frame in frame_dict.values():
        if frame['frame_type'] == 'CONNECTION_CLOSE':
            time = frame['time_elaps']
            connection_close_time_list.append(time)
            infos.append('quic error: ' + frame['quic_error'])

            if frame['direction'] == 'send':
                actions.append('Client_SEND_CONNECTION_CLOSE')
            else:
                actions.append('Server_SEND_CONNECTION_CLOSE')

    source = ColumnDataSource(data={
        'x': connection_close_time_list,
        'y': [-1] * len(connection_close_time_list),
        'name': actions ,
        'info': infos
    })
    return source