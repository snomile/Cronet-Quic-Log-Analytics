import csv
import json

from process import constant_converter
from process.quic_entity import PacketReceived, PacketSent

IGNORE_EVENT_TYPE_LIST = [
    'QUIC_SESSION',
    'QUIC_SESSION_VERSION_NEGOTIATED',
    'CERT_CT_COMPLIANCE_CHECKED',
    'QUIC_SESSION_PACKET_AUTHENTICATED',
    'QUIC_SESSION_PADDING_FRAME_SENT',
    'QUIC_SESSION_PADDING_FRAME_RECEIVED',
    'SIGNED_CERTIFICATE_TIMESTAMPS_CHECKED',
    'CERT_VERIFIER_REQUEST',
    'CERT_VERIFIER_REQUEST_BOUND_TO_JOB',
    'QUIC_SESSION_CERTIFICATE_VERIFIED'
]

class QuicConnection:
    def __init__(self, host, dns_begin_time, dns_end_time, cronet_event_list, data_converted_path, filename_without_ext):
        self.general_info = {'host': host, 'dns_begin_time': 0, 'dns_duration': dns_end_time- dns_begin_time}
        self.request_start_time_int = dns_begin_time
        self.general_info['start_time'] = constant_converter.get_readable_time(dns_begin_time)
        self.cronet_event_list = [cronet_event for cronet_event in cronet_event_list if cronet_event.event_type not in IGNORE_EVENT_TYPE_LIST]
        self.data_converted_path = data_converted_path
        self.packets = []
        self.frames = [] #TODO remove this element
        self.frame_sent_dict = {}
        self.frame_received_dict = {}
        self.stream_dict = {}
        self.packet_sent_dict = {}
        self.packet_received_dict = {}
        self.session_info_dict = {}

        #convert event to quic entities
        self.extract_packet()
        self.tag_packet_by_ack()
        self.extract_retransmission_info()
        self.extract_general_info()
        self.extract_download_time()
        self.extract_server_packet_loss_rate()

        #print general info
        for key,value in self.general_info.items():
            if isinstance(value,dict):  #CHLO and SHLO
                 print(key,':', value['quic_crypto_handshake_message'])
            else:
                print(key,':',value)

        self.validate()

        #generate save file path
        quic_session_starttime = cronet_event_list[0].time_int
        safe_filename_without_ext = filename_without_ext.replace(':', '_')  #convert : to _ to avoid corrupting the file system
        self.fullpath_json_file = '%s%s_%s_quic_connection.json' % (data_converted_path, host, quic_session_starttime)
        self.general_info['json_name'] = '%s_%s_quic_connection.json' % (host, quic_session_starttime)
        self.fullpath_general_info_json_file = '%s%s_%s_general_info.json' % (data_converted_path, host, quic_session_starttime)
        # self.fullpath_quic_frame_csv_file = '%s%s_%s_quic_frame.csv' % (data_converted_path, host, quic_session_starttime)
        # self.fullpath_quic_packet_csv_file = '%s%s_%s_quic_packet.csv' % (data_converted_path, host, quic_session_starttime)
        # self.fullpath_quic_session_csv_file = '%s%s_%s_quic_session.csv' % (data_converted_path, host, quic_session_starttime)


    def extract_general_info(self):
        chlo_event_index = 0
        shlo_event_index = 0
        last_chlo = None
        last_shlo = None
        handshake_start_time = 0
        handshake_end_time = 0

        self.general_info['session_type'] = None

        for event in self.cronet_event_list:
            if event.event_type in ['QUIC_SESSION_CRYPTO_HANDSHAKE_MESSAGE_SENT', 'QUIC_SESSION_CRYPTO_HANDSHAKE_MESSAGE_RECEIVED']:
                if self.general_info['session_type'] is None and event.event_type == 'QUIC_SESSION_CRYPTO_HANDSHAKE_MESSAGE_SENT':
                    self.general_info['session_type'] = 'client'
                else:
                    self.general_info['session_type'] = 'server'

                if 'CHLO' in event.other_data_str:
                    if chlo_event_index == 0:
                        handshake_start_time = event.time_int
                        self.general_info['handshake_start_time'] = handshake_start_time
                    chlo_event_index += 1
                    self.general_info['CHLO%s' % chlo_event_index] = event.other_data['params']
                    last_chlo = event.other_data['params']
                else:
                    handshake_end_time = event.time_int
                    shlo_event_index += 1
                    self.general_info['SHLO%s' % chlo_event_index] = event.other_data['params']
                    sttl = constant_converter.find_key_value(event.other_data['params']['quic_crypto_handshake_message'],'STTL')
                    if sttl:
                        self.general_info['STTL'] = sttl
                    expy = constant_converter.find_key_value(event.other_data['params']['quic_crypto_handshake_message'],'EXPY')
                    if sttl:
                        self.general_info['EXPY'] = expy
                    last_shlo = event.other_data['params']
            elif event.event_type == 'QUIC_SESSION_VERSION_NEGOTIATED':
                self.general_info['version'] = event.other_data['params']['version']

        #extract stat info
        self.general_info['handshake_round'] = shlo_event_index
        if handshake_end_time == 0:
            self.general_info['handshake_duration'] = -1
        else:
            self.general_info['handshake_duration'] = handshake_end_time - handshake_start_time
        self.general_info['handshake_retransmission_count'] = 0 #TODO
        self.general_info['packet_sent_count'] = len(self.packet_sent_dict)
        self.general_info['packet_receive_count'] = len(self.packet_received_dict)
        self.general_info['stream_count'] = len(self.stream_dict)
        self.general_info['frame_sent_count'] = len(self.frame_sent_dict)
        self.general_info['frame_receive_count'] = len(self.frame_received_dict)
        self.general_info['first_byte_duration'] = 0 #TODO
        self.general_info['first_byte_duration_after_handshake'] = 0  # TODO
        self.general_info['body'] = '' #TODO

        # exact SFCW and CFCW
        self.general_info['client_cfcw'] = 9999999999  # default a large value so it will not appear on the graph
        self.general_info['client_sfcw'] = 9999999999
        self.general_info['server_cfcw'] = 9999999999
        self.general_info['server_sfcw'] = 9999999999

        if last_chlo and 'quic_crypto_handshake_message' in last_chlo.keys():
            last_chlo_infos = last_chlo['quic_crypto_handshake_message'].split('\n')
            for info in last_chlo_infos:
                if 'CFCW' in info:
                    self.general_info['client_cfcw'] = int(info.split(': ')[1])
                if 'SFCW' in info:
                    self.general_info['client_sfcw'] = int(info.split(': ')[1])

        if last_shlo and 'quic_crypto_handshake_message' in last_shlo.keys():
            last_shlo_infos = last_shlo['quic_crypto_handshake_message'].split('\n')
            for info in last_shlo_infos:
                if 'CFCW' in info:
                    self.general_info['server_cfcw'] = int(info.split(': ')[1])
                if 'SFCW' in info:
                    self.general_info['server_sfcw'] = int(info.split(': ')[1])


    def extract_server_packet_loss_rate(self):
        if len(self.packet_received_dict) == 0:
            self.general_info['receive_packet_loss_rate'] = 0
        else:
            total_loss_receive_packet = 0
            last_receive_packet_number = 0
            for packet_number, packet in self.packet_received_dict.items():
                total_loss_receive_packet = total_loss_receive_packet + packet_number - (last_receive_packet_number + 1)
                last_receive_packet_number = packet_number
            self.general_info['receive_packet_loss_rate'] = round(1.0*total_loss_receive_packet/len(self.packet_received_dict), 3)

    def extract_download_time(self):
        last_quic_session_packet_received_time = 0
        for frame_id, frame in self.frame_received_dict.items():
            if frame.stream_id != 'N/A' and self.packet_received_dict[frame.packet_number].time_int > last_quic_session_packet_received_time:
                last_quic_session_packet_received_time = self.packet_received_dict[frame.packet_number].time_int
        if last_quic_session_packet_received_time == 0:
            self.general_info['download_duration'] = -1
        else:
            self.general_info['download_duration'] = last_quic_session_packet_received_time - self.general_info['handshake_start_time']


    def extract_packet(self):
        i = 0
        event_list = self.cronet_event_list.copy()
        length = len(event_list)
        print('events to process: ', length)

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
                #calc server caused delay
                ack_delay_by_server = round(frame.delta_time_largest_observed_us/1000.0, 3)

                #tag packet with ack delay
                latest_largest_observed_packet = frame.largest_observed
                for i in range(largest_unobserved_packet, latest_largest_observed_packet+1):
                    packet = self.packet_sent_dict[i]
                    packet.ack_by_frame_id = frame.frame_id
                    frame_time_elaps = self.packet_received_dict[frame.packet_number].time_elaps
                    packet.ack_delay = frame_time_elaps - packet.time_elaps
                    packet.ack_delay_server = ack_delay_by_server
                    frame.ack_packet_number_list.append(packet.packet_number)
                largest_unobserved_packet = latest_largest_observed_packet + 1

                #tag packet with lost tag
                if len(frame.missing_packets) > 0:
                    for packet_number in frame.missing_packets: # TODO check the consistency with QUIC_SESSION_PACKET_LOST
                        lost_packet = self.packet_sent_dict[packet_number]
                        lost_packet.is_lost = True

    def extract_retransmission_info(self):
        total_send_packet_number = len(self.packet_sent_dict)
        if total_send_packet_number == 0:
            self.general_info['retransmission_rate'] = 0
            self.general_info['lost_rate'] = 0
        else:
            retransmission_number = 0
            lost_number = 0
            for packet in self.packet_sent_dict.values():
                if packet.transmission_type != 'NOT_RETRANSMISSION':
                    retransmission_number += 1
                if packet.is_lost:
                    lost_number += 1
            self.general_info['retransmission_rate'] = round(float(retransmission_number)/total_send_packet_number,3)
            self.general_info['lost_rate'] = round(float(lost_number) / total_send_packet_number, 3)

    def add_packet(self,packet):
        self.packets.append(packet)

    def add_frame(self,frame):
        self.frames.append(frame)
        stream_id = frame.stream_id
        if stream_id in self.stream_dict.keys():
            self.stream_dict[stream_id].append(frame.frame_id)
        else:
            self.stream_dict[stream_id] = [frame.frame_id]
        if frame.direction == 'send':
            self.frame_sent_dict[frame.frame_id] = frame
        else:
            self.frame_received_dict[frame.frame_id] = frame

    def validate(self):
        print('validating...')
        ack_frame_receive_count = 0
        ack_frame_send_count = 0
        packet_receive_count = 0
        packet_sent_count = 0
        window_update_frame_receive_count = 0
        window_update_frame_send_count = 0
        for event in self.cronet_event_list:
            if event.event_type == 'QUIC_SESSION_PACKET_RECEIVED':
                packet_receive_count += 1
            elif event.event_type == 'QUIC_SESSION_PACKET_SENT':
                packet_sent_count += 1
            elif event.event_type == 'QUIC_SESSION_ACK_FRAME_RECEIVED':
                ack_frame_receive_count += 1
            elif event.event_type == 'QUIC_SESSION_ACK_FRAME_SENT':
                ack_frame_send_count += 1
            elif event.event_type == 'QUIC_SESSION_WINDOW_UPDATE_FRAME_RECEIVED':
                window_update_frame_receive_count += 1
            elif event.event_type == 'QUIC_SESSION_WINDOW_UPDATE_FRAME_SENT':
                window_update_frame_send_count += 1

        ack_frame_receive_count_after_processing = 0
        ack_frame_send_count_after_processing = 0
        windows_update_frame_receive_count_after_processing = 0
        windows_update_frame_send_count_after_processing = 0
        for frame in self.frames:
            if frame.frame_type == 'ACK' and frame.direction == 'receive':
                ack_frame_receive_count_after_processing += 1
            if frame.frame_type == 'ACK' and frame.direction == 'send':
                ack_frame_send_count_after_processing += 1
            if frame.frame_type == 'WINDOW_UPDATE' and frame.direction == 'receive':
                windows_update_frame_receive_count_after_processing += 1
            if frame.frame_type == 'WINDOW_UPDATE' and frame.direction == 'send':
                windows_update_frame_send_count_after_processing += 1
        print('QUIC entity count from chrome log:')
        print('PACKET_RECEIVED: ',packet_receive_count)
        print('PACKET_SENT: ',packet_sent_count)
        print('ACK_FRAME_RECEIVED: ', ack_frame_receive_count)
        print('ACK_FRAME_SENT: ', ack_frame_send_count)
        print('WINDOW_UPDATE_FRAME_RECEIVED: ', window_update_frame_receive_count)
        print('WINDOW_UPDATE_FRAME_SENT: ', window_update_frame_send_count)
        print('-------------------')
        print('quic entity count after processing:')
        print('PACKET_RECEIVED: ',len(self.packet_received_dict))
        print('PACKET_SENT: ',len(self.packet_sent_dict))
        print('ACK_FRAME_RECEIVED: ', ack_frame_receive_count_after_processing)
        print('ACK_FRAME_SENT: ', ack_frame_send_count_after_processing)
        print('WINDOW_UPDATE_FRAME_RECEIVED: ', windows_update_frame_receive_count_after_processing)
        print('WINDOW_UPDATE_FRAME_SENT: ', windows_update_frame_send_count_after_processing)

        if packet_receive_count != len(self.packet_received_dict) \
                or packet_sent_count != len(self.packet_sent_dict) \
                or ack_frame_receive_count != ack_frame_receive_count_after_processing \
                or ack_frame_send_count != ack_frame_send_count_after_processing \
                or windows_update_frame_receive_count_after_processing != windows_update_frame_receive_count_after_processing \
                or window_update_frame_send_count != windows_update_frame_send_count_after_processing:
            print('ERROR: count mismatch, check log and program please')
        else:
            print('validate success')


    def save(self):
        # with open(self.fullpath_quic_session_csv_file, 'wt') as f:
        #     cw = csv.writer(f)
        #     for event in self.cronet_event_list:
        #         cw.writerow(event.get_info_list())
        #
        # with open(self.fullpath_quic_packet_csv_file, 'wt') as f:
        #     cw = csv.writer(f)
        #     cw.writerow(['Time', 'Time Elaps', 'Type', 'Packet Number','Size'])
        #     for packet in self.packets:
        #         cw.writerow(packet.get_info_list())
        #
        # with open(self.fullpath_quic_frame_csv_file, 'wt') as f:
        #     cw = csv.writer(f)
        #     cw.writerow(['Time Elaps','Packet Number','ACK delay', 'Frame type', 'Direction','Stream_id'])
        #     for frame in self.frames:
        #         if frame.direction == 'receive':
        #             packet = self.packet_received_dict[frame.packet_number]
        #             csv_info = [packet.time_elaps, packet.packet_number, 'N/A']
        #         else:
        #             packet = self.packet_sent_dict[frame.packet_number]
        #             csv_info = [packet.time_elaps,packet.packet_number,packet.ack_delay]
        #         csv_info.extend(frame.get_info_list())
        #         cw.writerow(csv_info)

        #construct json obj
        print('generate json at', self.fullpath_json_file)
        json_obj = {
            'general_info': self.general_info,
            'packets_sent': [],
            'packet_sent_dict': {},
            'packets_received': [],
            'packet_received_dict': {},
            'stream_dict': self.stream_dict,
            'frame_dict': {frame.frame_id: frame.__dict__ for frame in self.frames}
        }
        for packet in self.packet_sent_dict.values():
            packet_json_obj = {
                'direction':'send',
                'elaps': packet.time_elaps,
                'time': packet.time_elaps,
                'time_h': packet.time_readable,
                'number': packet.packet_number,
                'ack_by_frame' : packet.ack_by_frame_id,
                'ack_delay': packet.ack_delay,
                'ack_delay_server': packet.ack_delay_server,
                'length': packet.size,
                'frame_ids':[frame.frame_id for frame in packet.frames],
                'is_lost': packet.is_lost,
                'info': packet.get_info_list(),
                'info_str': packet.info_str,
                'is_chlo': packet.is_chlo,
                'is_shlo': packet.is_shlo,
                'transmission_type': packet.transmission_type
            }
            json_obj['packets_sent'].append(packet_json_obj)
            json_obj['packet_sent_dict'][packet.packet_number] = packet_json_obj

        for packet in self.packet_received_dict.values():
            packet_json_obj = {
                'direction':'receive',
                'time': packet.time_elaps,
                'time_h': packet.time_readable,
                'number': packet.packet_number,
                'info': packet.get_info_list(),
                'length': packet.size,
                'frame_ids':[frame.frame_id for frame in packet.frames],
                'info_str': packet.info_str,
                'is_chlo': packet.is_chlo,
                'is_shlo': packet.is_shlo
            }
            json_obj['packets_received'].append(packet_json_obj)
            json_obj['packet_received_dict'][packet.packet_number] = packet_json_obj


        with open(self.fullpath_general_info_json_file, "w") as f:
            json.dump(self.general_info, f)

        with open(self.fullpath_json_file, "w") as f:
            json.dump(json_obj, f)

        return self.fullpath_json_file