class PacketReceived:
    def __init__(self, quic_connection, packet_received_event, relate_events):
        self.relate_events = relate_events.copy()
        if self.relate_events[0].event_type != 'QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED':
            raise BaseException('QUIC_SESSION_PACKET_RECEIVED event followed by illigal event type: %s' % self.relate_events[0].event_type)

        self.time_int = packet_received_event.time_int
        self.time_elaps = self.time_int - quic_connection.start_time_int
        self.type = 'PacketReceived'
        self.source_id = packet_received_event.source_id
        self.peer_address = packet_received_event.other_data['params']['peer_address']
        self.self_address = packet_received_event.other_data['params']['self_address']
        self.size = packet_received_event.other_data['params']['size']

        self.connection_id = self.relate_events[0].other_data['params']['connection_id']
        self.packet_number = self.relate_events[0].other_data['params']['packet_number']
        self.reset_flag = self.relate_events[0].other_data['params']['reset_flag']
        self.version_flag = self.relate_events[0].other_data['params']['version_flag']
        self.relate_events.pop(0)

        self.frames = []
        self.init_frame(self.relate_events)
        for i in range(len(self.frames)):
            frame = self.frames[i]
            frame.frame_id = '%s_%s_%s' % (self.type, self.packet_number, i)
            quic_connection.add_frame(frame)

    def init_frame(self, related_sent_event):
        events_buffer = []
        last_frame_received_event = None
        for event in related_sent_event:
            if 'FRAME_RECEIVED' in event.event_type or event == related_sent_event[-1]: #if current event is the last event, the last QuicFrame must be create before loop end
                if last_frame_received_event != None:
                    frame = QuicFrame(self.packet_number, self.time_elaps, last_frame_received_event, events_buffer)
                    self.frames.append(frame)
                    events_buffer = []
                last_frame_received_event = event
            else:
                events_buffer.append(event)

    def get_info_list(self):
        return [
            self.time_int,
            self.time_elaps,
            self.type,
            self.packet_number,
            self.size,
            self.peer_address,
            self.self_address,
            self.connection_id,
            self.reset_flag,
            self.version_flag,
            [frame.get_info_list() for frame in self.frames]
        ]


class PacketSent:
    def __init__(self, quic_connection, QUIC_SESSION_PACKET_SENT_event, related_event):
        self.time_int = QUIC_SESSION_PACKET_SENT_event.time_int
        self.time_elaps = self.time_int - quic_connection.start_time_int
        self.type = 'PacketSent'
        self.source_id = QUIC_SESSION_PACKET_SENT_event.source_id
        self.packet_number = QUIC_SESSION_PACKET_SENT_event.other_data['params']['packet_number']
        self.size = QUIC_SESSION_PACKET_SENT_event.other_data['params']['size']
        self.transmission_type = QUIC_SESSION_PACKET_SENT_event.other_data['params']['transmission_type']
        self.ack_by_frame_id = 'N/A'
        self.ack_delay = 0 # ms

        self.frames = []
        self.init_frame(related_event.copy())
        for i in range(len(self.frames)):
            frame = self.frames[i]
            frame.frame_id = '%s_%s_%s' % (self.type, self.packet_number, i)
            quic_connection.add_frame(frame)

    def init_frame(self, related_sent_event):
        events_buffer = []
        for event in related_sent_event:
            if 'FRAME_SENT' in event.event_type:
                frame = QuicFrame(self.packet_number, self.time_elaps,event, events_buffer)
                self.frames.append(frame)
                events_buffer = []
            else:
                events_buffer.append(event)

    def get_info_list(self):
        return [
            self.time_int,
            self.time_elaps,
            self.type,
            self.packet_number,
            self.size,
            self.ack_delay,
            self.transmission_type,
            [frame.get_info_list() for frame in self.frames]
        ]


class QuicStream:
    def __init__(self):
        self.frames = []

    def add_frame(self,frame):
        self.frames.append(frame)


class QuicFrame:
    def __init__(self,packet_number,time_elaps, event, relate_events):
        relate_events = relate_events.copy()
        self.info_list = []
        self.frame_type = None
        self.frame_id = None
        self.packet_number = packet_number
        self.time_elaps = time_elaps

        if event.event_type == 'QUIC_SESSION_STREAM_FRAME_SENT':
            self.frame_type = 'STREAM'
            self.direction = 'send'
            self.stream_id = event.other_data['params']['stream_id']
            self.length = event.other_data['params']['length']
            self.offset = event.other_data['params']['offset']
            self.info_list.extend([self.frame_type,self.direction,self.stream_id,'length: %s' % self.length, 'offset: %s' % self.offset])
        elif event.event_type == 'QUIC_SESSION_STREAM_FRAME_RECEIVED':
            self.frame_type = 'STREAM'
            self.direction = 'receive'
            self.stream_id = event.other_data['params']['stream_id']
            self.length = event.other_data['params']['length']
            self.offset = event.other_data['params']['offset']
            self.info_list.extend([self.frame_type,self.direction,self.stream_id,'length: %s' % self.length, 'offset: %s' % self.offset])
        elif event.event_type == 'QUIC_SESSION_ACK_FRAME_SENT':
            self.frame_type = 'ACK'
            self.direction = 'send'
            self.stream_id = 'N/A'
            self.largest_observed = event.other_data['params']['largest_observed']
            self.missing_packets = event.other_data['params']['missing_packets']
            self.delta_time_largest_observed_us = event.other_data['params']['delta_time_largest_observed_us']
            self.received_packet_times = event.other_data['params']['received_packet_times']
            self.info_list.extend([self.frame_type,self.direction,self.stream_id,'largest_observed: %s' % self.largest_observed,'missing_packets: %s' % self.missing_packets,'delta_time_largest_observed_us: %s' % self.delta_time_largest_observed_us,'received_packet_times: %s' % self.received_packet_times])
        elif event.event_type =='QUIC_SESSION_ACK_FRAME_RECEIVED':
            self.frame_type = 'ACK'
            self.direction = 'receive'
            self.stream_id = 'N/A'
            self.largest_observed = event.other_data['params']['largest_observed']
            self.missing_packets = event.other_data['params']['missing_packets']
            self.delta_time_largest_observed_us = event.other_data['params']['delta_time_largest_observed_us']
            self.received_packet_times = event.other_data['params']['received_packet_times']
            self.ack_packet_number_list = []
            self.info_list.extend([self.frame_type,self.direction,self.stream_id,'largest_observed: %s' % self.largest_observed,'missing_packets: %s' % self.missing_packets,'delta_time_largest_observed_us: %s' % self.delta_time_largest_observed_us,'received_packet_times: %s' % self.received_packet_times])
        elif event.event_type == 'QUIC_SESSION_BLOCKED_FRAME_SENT':
            self.frame_type = 'BLOCKED'
            self.direction = 'send'
            self.stream_id = event.other_data['params']['stream_id']
            self.info_list.extend([self.frame_type,self.direction,self.stream_id])
        elif event.event_type== 'QUIC_SESSION_WINDOW_UPDATE_FRAME_RECEIVED':
            self.frame_type = 'WINDOW_UPDATE'
            self.direction = 'receive'
            self.stream_id = event.other_data['params']['stream_id']
            self.byte_offset = event.other_data['params']['byte_offset']
            self.info_list.extend([self.frame_type,self.direction,self.stream_id, 'byte_offset: %s' % self.byte_offset])
        else:
            print('WARN: unhandled frame',event.event_type)
        self.info_list.extend([event.get_info_list() for event in relate_events])


    def get_info_list(self):
        return self.info_list