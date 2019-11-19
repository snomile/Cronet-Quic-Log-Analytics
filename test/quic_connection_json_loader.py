import json

if __name__ == '__main__':
    file_path = "../data_converted/quic-gh2ir_quic_connection.json"
    with open(file_path, 'r') as load_f:
        load_dict = json.load(load_f)
        print('load packet_sent: ', len(load_dict['packets_sent']))
        print('load packet_received: ', len(load_dict['packets_received']))