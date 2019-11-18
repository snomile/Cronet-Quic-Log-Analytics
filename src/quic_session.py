import json


class packet_received:
    def __init__(self,QUIC_SESSION_PACKET_RECEIVED_event,QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED_event):
        self.peer_address = QUIC_SESSION_PACKET_RECEIVED_event['params']['peer_address']
        self.self_address = QUIC_SESSION_PACKET_RECEIVED_event['params']['self_address']
        self.size = QUIC_SESSION_PACKET_RECEIVED_event['params']['size']

        self.connection_id = QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED_event['params']['connection_id']
        self.packet_number = QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED_event['params']['packet_number']
        self.reset_flag = QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED_event['params']['reset_flag']
        self.version_flag = QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED_event['params']['version_flag']

    def to_string(self):
        return json.dumps(self.__dict__)

if __name__ == '__main__':
    packet_received_event = json.loads('{"params": {"peer_address": "34.102.205.215:443", "self_address": "192.168.100.10:64543", "size": 20}, "phase": 0, "source": {"id": 16, "type": 10}}')
    header_received_event = json.loads('{"params": {"connection_id": "0", "header_format": "GOOGLE_QUIC_PACKET", "packet_number": 5, "reset_flag": 0, "version_flag": 0}, "phase": 0, "source": {"id": 16, "type": 10}}')
    event_obj = packet_received(packet_received_event,header_received_event)

    print(event_obj.to_string())

