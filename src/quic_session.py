import csv
import json

ingore_event_type_list = [
    'QUIC_SESSION_PACKET_AUTHENTICATED'
]


#TODO clean illgal peer_address data
class QuicSession:
    def __init__(self,chrome_event_list,persistant_file_path):
        self.persistant_file_path = persistant_file_path

        # find quic session start time
        for event in chrome_event_list:
            if event.event_type == 'QUIC_SESSION':
                self.start_time_int = event.time_int
                break

        #generate packets
        self.quic_chrome_event_list = []
        self.packet_list = []
        self.init_by_chrome_event(chrome_event_list)

    def init_by_chrome_event(self,event_list):
        i = 0
        length = len(event_list)
        print('events to process: ',length)
        while i < length:
            event = event_list[i]
            if event.event_type not in ingore_event_type_list and event.source_type == 'QUIC_SESSION':
                self.quic_chrome_event_list.append(event)

                if event.event_type == 'QUIC_SESSION_PACKET_RECEIVED':
                    next_event = event_list[i+1]
                    if next_event.event_type != 'QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED':
                        raise BaseException('packet received but no QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED event follows')
                    else:
                        packet_received = PacketReceived(event, next_event)
                        self.add_packet(packet_received)
                        i += 1
                elif event.event_type == 'QUIC_SESSION_PACKET_SENT':
                    packet_sent = PacketSent(event)
                    self.add_packet(packet_sent)
                else:
                    print('ignore quic event: ', event.get_info_list())

                if i % 1000 == 0: print('event processed: ',i)
            else:
                print('ignore NONE quic event,', event.get_info_list())
            i += 1

    def add_packet(self,packet):
        packet.time_elaps = packet.time_int - self.start_time_int
        self.packet_list.append(packet)

    def save(self):
        with open(self.persistant_file_path +'_quic_session.csv', 'wt') as f:
            cw = csv.writer(f)
            for event in self.quic_chrome_event_list:
                cw.writerow(event.get_info_list())

        with open(self.persistant_file_path +'_quic_packet.csv', 'wt') as f:
            cw = csv.writer(f)
            for packet in self.packet_list:
                cw.writerow(packet.get_info_list())


class PacketReceived:
    def __init__(self, QUIC_SESSION_PACKET_RECEIVED_event,QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED_event):
        self.time_int = QUIC_SESSION_PACKET_RECEIVED_event.time_int
        self.time_elaps = 0
        self.type = 'PacketReceived'
        self.source_id = QUIC_SESSION_PACKET_RECEIVED_event.source_id
        self.peer_address = QUIC_SESSION_PACKET_RECEIVED_event.other_data['params']['peer_address']
        self.self_address = QUIC_SESSION_PACKET_RECEIVED_event.other_data['params']['self_address']
        self.size = QUIC_SESSION_PACKET_RECEIVED_event.other_data['params']['size']

        self.connection_id = QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED_event.other_data['params']['connection_id']
        self.packet_number = QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED_event.other_data['params']['packet_number']
        self.reset_flag = QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED_event.other_data['params']['reset_flag']
        self.version_flag = QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED_event.other_data['params']['version_flag']


    def to_string(self):
        return json.dumps(self.__dict__)

    def get_info_list(self):
        return [
            self.time_int,
            self.time_elaps,
            self.type,
            self.packet_number,
            self.source_id,
            self.size,
            self.peer_address,
            self.self_address,
            self.connection_id,
            self.reset_flag,
            self.version_flag
        ]


class PacketSent:
    def __init__(self, QUIC_SESSION_PACKET_SENT_event):
        self.time_int = QUIC_SESSION_PACKET_SENT_event.time_int
        self.time_elaps = 0
        self.type = 'PacketSent'
        self.source_id = QUIC_SESSION_PACKET_SENT_event.source_id
        self.packet_number = QUIC_SESSION_PACKET_SENT_event.other_data['params']['packet_number']
        self.size = QUIC_SESSION_PACKET_SENT_event.other_data['params']['size']
        self.transmission_type = QUIC_SESSION_PACKET_SENT_event.other_data['params']['transmission_type']

    def get_info_list(self):
        return [
            self.time_int,
            self.time_elaps,
            self.type,
            self.packet_number,
            self.source_id,
            self.size,
            self.transmission_type
        ]

class QuicFrame:
    pass


if __name__ == '__main__':
    packet_received_event = json.loads('{"params": {"peer_address": "34.102.205.215:443", "self_address": "192.168.100.10:64543", "size": 20}, "phase": 0, "source": {"id": 16, "type": 10}}')
    header_received_event = json.loads('{"params": {"connection_id": "0", "header_format": "GOOGLE_QUIC_PACKET", "packet_number": 5, "reset_flag": 0, "version_flag": 0}, "phase": 0, "source": {"id": 16, "type": 10}}')
    event_obj = PacketReceived(packet_received_event, header_received_event)
    print(event_obj.get_info_list())

    packet_sent_event = json.loads('{"params": {"encryption_level": "ENCRYPTION_INITIAL", "packet_number": 2, "sent_time_us": 87729807737, "size": 28, "transmission_type": "NOT_RETRANSMISSION"}, "phase": 0, "source": {"id": 16, "type": 10}}')
    event_obj = PacketSent(packet_sent_event)
    print(event_obj.get_info_list())

