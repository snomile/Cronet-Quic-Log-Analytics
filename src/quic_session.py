import csv
import json

from quic_entity import PacketReceived, PacketSent

ingore_event_type_list = [
    'QUIC_SESSION_PACKET_AUTHENTICATED',
    'QUIC_SESSION_PADDING_FRAME_SENT',
    'QUIC_SESSION_PADDING_FRAME_RECEIVED',
    'SIGNED_CERTIFICATE_TIMESTAMPS_CHECKED',
    'CERT_VERIFIER_REQUEST',
    'CERT_VERIFIER_REQUEST_BOUND_TO_JOB',
    'QUIC_SESSION_CERTIFICATE_VERIFIED'
]


class QuicConnection:
    def __init__(self,chrome_event_list,persistant_file_path):
        self.persistant_file_path = persistant_file_path
        self.quic_chrome_event_list = []
        self.general_info = {}

        #extract quic general info
        chlo_event_index = 0
        shlo_event_index = 0
        for event in chrome_event_list:
            if event.source_type == 'QUIC_SESSION' and event.event_type not in ingore_event_type_list:
                if event.event_type == 'QUIC_SESSION':
                    self.start_time_int = event.time_int
                    self.general_info['Start_time'] = event.time_int
                    self.general_info['Host'] = event.other_data['params']['host']
                    self.general_info['Port'] = event.other_data['params']['port']
                    print('quic session found')
                elif event.event_type == 'QUIC_SESSION_CRYPTO_HANDSHAKE_MESSAGE_SENT':
                    chlo_event_index += 1
                    self.general_info['CHLO%s' % chlo_event_index] = event.other_data['params']
                elif event.event_type == 'QUIC_SESSION_CRYPTO_HANDSHAKE_MESSAGE_RECEIVED':
                    shlo_event_index += 1
                    self.general_info['SHLO%s' % chlo_event_index] = event.other_data['params']
                elif event.event_type == 'QUIC_SESSION_VERSION_NEGOTIATED':
                    self.general_info['Version'] = event.other_data['params']['version']
                else:
                    self.quic_chrome_event_list.append(event)
            else:
                #print('ignore NONE quic event,', event.get_info_list())
                pass
        for key,value in self.general_info.items():
            if isinstance(value,dict):
                print(key,': ----------------------')
                for _key, _value in value.items():
                    print('\t',_key,':',_value)
            else:
                print(key,':',value)


        #construct packet/stream/frame data structure
        self.packets = []
        self.frames = []
        self.stream_dict = {}
        self.packet_sent_dict = {}
        self.packet_received_dict = {}
        self.construct_quic_data_structure(self.quic_chrome_event_list)
        self.tag_packet_by_ack()

    def construct_quic_data_structure(self, event_list):
        i = 0
        event_list = event_list.copy()
        length = len(event_list)
        print('events to process: ',length)

        sent_event_buffer = []
        received_event_buffer = []
        while i < length:
            event = event_list[i]
            if event.event_type == 'QUIC_SESSION_PACKET_RECEIVED':
                #search the next packet received event
                for j in range(i+1,length):
                    next_event = event_list[j]
                    if ('RECEIVED' in next_event.event_type or 'READ' in next_event.event_type) and next_event.event_type != 'QUIC_SESSION_PACKET_RECEIVED' :
                        received_event_buffer.append(next_event)
                    if next_event.event_type == 'QUIC_SESSION_PACKET_RECEIVED' or j == length-1: #j==length-1 means no more events to handle, so it's an exit point
                        packet_received = PacketReceived(self, event, received_event_buffer)
                        self.add_packet(packet_received)
                        self.packet_received_dict[packet_received.packet_number] = packet_received
                        for del_event in received_event_buffer:
                            event_list.remove(del_event)
                        length -= len(received_event_buffer)
                        received_event_buffer = []
                        break
            elif event.event_type == 'QUIC_SESSION_PACKET_SENT':
                packet_sent = PacketSent(self, event, sent_event_buffer)
                self.add_packet(packet_sent)
                self.packet_sent_dict[packet_sent.packet_number] = packet_sent
                sent_event_buffer = []
            elif 'SENT' in event.event_type or 'SEND' in event.event_type:
                sent_event_buffer.append(event)
            else:
                print('WARN: ignore quic event: ', event.get_info_list())
            i += 1

        print('quic session analyzation finished')
        print('packet: ', len(self.packets))
        print('stream: ', len(self.stream_dict.keys()))
        print('frame: ', len(self.frames))

    def tag_packet_by_ack(self):
        largest_unobserved_packet = 1
        for frame in self.frames:
            if frame.frame_type == 'ACK' and frame.direction == 'receive':
                latest_largest_observed_packet = frame.largest_observed
                for i in range(largest_unobserved_packet, latest_largest_observed_packet+1):
                    packet = self.packet_sent_dict[i]
                    packet.ack_by_frame_id = frame.frame_id
                    frame_time_elaps = self.packet_received_dict[frame.packet_number].time_elaps
                    packet.ack_delay = frame_time_elaps - packet.time_elaps
                largest_unobserved_packet = latest_largest_observed_packet + 1


    def add_packet(self,packet):
        packet.time_elaps = packet.time_int - self.start_time_int
        self.packets.append(packet)


    def add_frame(self,frame):
        self.frames.append(frame)
        stream_id = frame.stream_id
        if stream_id in self.stream_dict.keys():
            self.stream_dict[stream_id].append(frame.frame_id)
        else:
            self.stream_dict[stream_id] = [frame.frame_id]

    def get_general_info(self):
        for event in self.quic_chrome_event_list:
            self.general_info['']=''
        pass

    def save(self):
        print('saving quic_session.csv...')
        with open(self.persistant_file_path +'_quic_session.csv', 'wt') as f:
            cw = csv.writer(f)
            for event in self.quic_chrome_event_list:
                cw.writerow(event.get_info_list())

        print('saving quic_packet.csv...')
        with open(self.persistant_file_path +'_quic_packet.csv', 'wt') as f:
            cw = csv.writer(f)
            cw.writerow(['Time', 'Time Elaps', 'Type', 'Packet Number','Size'])
            for packet in self.packets:
                cw.writerow(packet.get_info_list())

        print('saving quic_frame.csv...')
        with open(self.persistant_file_path +'_quic_frame.csv', 'wt') as f:
            cw = csv.writer(f)
            cw.writerow(['Time Elaps','Packet Number','ACK delay', 'Frame type', 'Direction','Stream_id'])
            for frame in self.frames:
                if frame.direction == 'receive':
                    packet = self.packet_received_dict[frame.packet_number]
                    csv_info = [packet.time_elaps, packet.packet_number, 'N/A']
                else:
                    packet = self.packet_sent_dict[frame.packet_number]
                    csv_info = [packet.time_elaps,packet.packet_number,packet.ack_delay]
                csv_info.extend(frame.get_info_list())
                cw.writerow(csv_info)

        #construct json obj
        print('saving quic_connection.json...')
        json_obj = {
            'general_info' : self.general_info,
            'packets_sent': [],
            'packet_sent_dict' : {},
            'packets_received': [],
            'packet_received_dict': {},
            'stream_dict': self.stream_dict,
            'frame_dict': {frame.frame_id: frame.__dict__ for frame in self.frames}
        }
        for packet in self.packet_sent_dict.values():
            packet_json_obj = {
                'direction':'send',
                'time': packet.time_elaps,
                'number': packet.packet_number,
                'ack_by_frame' : packet.ack_by_frame_id,
                'ack_delay': packet.ack_delay,
                'info': packet.get_info_list(),
                'length': packet.size,
                'frame_ids':[frame.frame_id for frame in packet.frames]
            }
            json_obj['packets_sent'].append(packet_json_obj)
            json_obj['packet_sent_dict'][packet.packet_number] = packet_json_obj

        for packet in self.packet_received_dict.values():
            packet_json_obj = {
                'direction':'receive',
                'time': packet.time_elaps,
                'number': packet.packet_number,
                'info': packet.get_info_list(),
                'length': packet.size,
                'frame_ids':[frame.frame_id for frame in packet.frames]
            }
            json_obj['packets_received'].append(packet_json_obj)
            json_obj['packet_received_dict'][packet.packet_number] = packet_json_obj

        with open(self.persistant_file_path +'_quic_connection.json', "w") as f:
            json.dump(json_obj, f)