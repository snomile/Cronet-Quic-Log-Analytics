#TODO:
# 1) packet on the fly in time secquence, with CFCW/SFCW size info overlay
# 2) ack distence in time and packet number（发现ack间距大，而CFCW和SFCW又没有变大的问题）
import json
import os

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

frame_dict = {}
packets_sent = []

def init(original_file_path):
    global frame_dict,packets_sent
    (filepath, tempfilename) = os.path.split(original_file_path)
    (filename, extension) = os.path.splitext(tempfilename)
    with open('../data_converted/' + filename+ '_quic_connection.json', 'r') as load_f:
        load_dict = json.load(load_f)
        frame_dict = load_dict['frame_dict']
        packets_sent = load_dict['packets_sent']

    print('load general info: ', len(load_dict['general_info']))
    print('load packet_sent: ', len(packets_sent))
    print('load packet_received: ', len(load_dict['packets_received']))
    print('load stream_dict: ', len(load_dict['stream_dict']))
    print('load frame_dict: ', len(frame_dict))

def show():
    time_sequence = []
    ack_delay_total = []
    ack_delay_server = []
    for packet in packets_sent:
        time_sequence.append(packet['time'])
        ack_delay_total.append(packet['ack_delay'])
        ack_frame_id = packet['ack_by_frame']
        if ack_frame_id == 'N/A':
            if packet['info'][7][0][0] == 'ACK':
                ack_delay_server.append(0) # the last ack packet won't be acked, manually set the ack_delay_server to 0
            else:
                print('WARN: Possible error packet: ', packet['number'], ', which is not ACKed')
        else:
            ack_frame = frame_dict[ack_frame_id]
            ack_delay_server.append(round(float(ack_frame['delta_time_largest_observed_us'])/1000,3))


    plt.plot(time_sequence, ack_delay_total, label='packet ack delay (roughly RTT)')
    plt.plot(time_sequence, ack_delay_server, label='server caused ack delay')
    plt.legend()
    plt.show()





if __name__ == '__main__':
    init("../data_original/quic-gh2ir.json")
    show()
