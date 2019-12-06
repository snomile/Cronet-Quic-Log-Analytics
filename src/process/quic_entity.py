from process import constant_converter


class Packet:
    def __init__(self, quic_connection, main_event, relate_events):
        self.time_int = main_event.time_int
        self.time_elaps = self.time_int - quic_connection.request_start_time_int
        self.time_readable = constant_converter.get_readable_time(self.time_int)
        self.source_id = main_event.source_id
        self.size = main_event.other_data['params']['size']
        self.frames = []
        self.all_event = [main_event]
        self.all_event.extend(relate_events)
        for event in self.all_event:
            if 'packet_number' in event.other_data['params'].keys():
                self.packet_number = event.other_data['params']['packet_number']
                break
        self.info_str = ''.join([event.other_data_str for event in self.all_event])


class PacketReceived(Packet):
    def __init__(self, quic_connection, event, relate_events):
        Packet.__init__(self, quic_connection, event, relate_events)

        self.type = 'PacketReceived'
        self.relate_events = relate_events.copy()
        self.connection_id = self.relate_events[0].other_data['params']['connection_id']
        self.reset_flag = self.relate_events[0].other_data['params']['reset_flag']
        self.version_flag = self.relate_events[0].other_data['params']['version_flag']
        self.is_shlo = False
        #self.relate_events.pop(0)
        for event in self.all_event:
            if event.event_type == 'QUIC_SESSION_CRYPTO_HANDSHAKE_MESSAGE_RECEIVED':
                self.is_shlo = True

        self.init_frame(self.relate_events)
        for i in range(len(self.frames)):
            frame = self.frames[i]
            frame.frame_id = '%s_%s_%s' % (self.type, self.packet_number, i)
            quic_connection.add_frame(frame)

    def init_frame(self, related_event):
        #find all frame received event
        frame_received_event_index_list = []
        for i in range(len(related_event)):
            event = related_event[i]
            if 'FRAME_RECEIVED' in event.event_type:
                frame_received_event_index_list.append(i)

        for i in range(len(frame_received_event_index_list)):
            index = frame_received_event_index_list[i]
            if i == len(frame_received_event_index_list) -1:  #for the last frame received event, the rest packet relate event all belongs to the frame
                next_index = len(related_event)-1
            else:
                next_index = frame_received_event_index_list[i+1]
            events_belong_to_frame = related_event[index + 1: next_index - 1]
            frame = QuicFrame(self.packet_number, self.time_elaps, related_event[index], events_belong_to_frame)
            self.frames.append(frame)


    def get_info_list(self):
        return [
            self.time_int,
            self.time_elaps,
            self.type,
            self.packet_number,
            self.size,
            self.connection_id,
            self.reset_flag,
            self.version_flag,
            [frame.get_info_list() for frame in self.frames]
        ]


class PacketSent(Packet):
    def __init__(self, quic_connection, event, relate_events):
        Packet.__init__(self, quic_connection, event, relate_events)

        #self.time_elaps_since_session_init = event.time_elaps
        self.type = 'PacketSent'
        self.transmission_type = event.other_data['params']['transmission_type']
        self.ack_by_frame_id = 'N/A'
        self.ack_delay = 0  # ms, init by quic_session.tag_packet_by_ack
        self.ack_delay_server = 0  # ms
        self.is_lost = False
        self.is_chlo = False
        #self.relate_events.pop(0)
        for event in self.all_event:
            if event.event_type == 'QUIC_SESSION_CRYPTO_HANDSHAKE_MESSAGE_SENT':
                self.is_chlo = True

        self.init_frame(relate_events.copy())
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
            self.ack_delay_server,
            self.transmission_type,
            [frame.get_info_list() for frame in self.frames]
        ]


class QuicFrame:
    def __init__(self,packet_number,time_elaps, event, relate_events):
        relate_events = relate_events.copy()
        self.info_list = []
        self.frame_type = None
        self.frame_id = None
        self.packet_number = packet_number
        self.time_elaps = time_elaps

        all_event = [event]
        all_event.extend(relate_events)
        self.frame_info_str = ''.join([event.other_data_str for event in all_event])

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
        elif event.event_type== 'QUIC_SESSION_WINDOW_UPDATE_FRAME_SENT':
            self.frame_type = 'WINDOW_UPDATE'
            self.direction = 'send'
            self.stream_id = event.other_data['params']['stream_id']
            self.byte_offset = event.other_data['params']['byte_offset']
            self.info_list.extend([self.frame_type, self.direction, self.stream_id, 'byte_offset: %s' % self.byte_offset])
        elif event.event_type == 'QUIC_SESSION_PING_FRAME_SENT':
            self.frame_type = 'PING'
            self.direction = 'send'
            self.stream_id = 'N/A'
            self.info_list.extend([self.frame_type, self.direction, self.stream_id])
        elif event.event_type == 'QUIC_SESSION_PING_FRAME_RECEIVED':
            self.frame_type = 'PING'
            self.direction = 'receive'
            self.stream_id = 'N/A'
            self.info_list.extend([self.frame_type, self.direction, self.stream_id])
        elif event.event_type == 'QUIC_SESSION_CONNECTION_CLOSE_FRAME_SENT':
            self.frame_type = 'CONNECTION_CLOSE'
            self.direction = 'send'
            self.stream_id = 'N/A'
            self.details = event.other_data['params']['details']
            self.quic_error = constant_converter.get_quic_error(event.other_data['params']['quic_error'])
            self.info_list.extend([self.frame_type, self.direction, self.stream_id,self.details,self.quic_error])
        elif event.event_type == 'QUIC_SESSION_RST_STREAM_FRAME_SENT':
            self.frame_type = 'RST'
            self.direction = 'send'
            self.stream_id = event.other_data['params']['stream_id']
            self.offset = event.other_data['params']['offset']
            self.quic_rst_stream_error = constant_converter.get_quic_rst_error(event.other_data['params']['quic_rst_stream_error'])
            self.info_list.extend([self.frame_type, self.direction, self.stream_id,self.offset,self.quic_rst_stream_error])
        elif event.event_type == 'QUIC_SESSION_RST_STREAM_FRAME_RECEIVED':
            self.frame_type = 'RST'
            self.direction = 'receive'
            self.stream_id = event.other_data['params']['stream_id']
            self.offset = event.other_data['params']['offset']
            self.quic_rst_stream_error = constant_converter.get_quic_rst_error(event.other_data['params']['quic_rst_stream_error'])
            self.info_list.extend([self.frame_type, self.direction, self.stream_id, self.offset, self.quic_rst_stream_error])
        else:
            print('WARN: unhandled frame',event.event_type)

        self.info_list = {}
        for event in relate_events:
            self.info_list[event.event_type] = event.get_info_list()

    def get_info_list(self):
        return self.info_list