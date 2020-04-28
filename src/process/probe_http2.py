

def process_http2_session(http2_sessions, sockets):
    http2s = []
    for key, values in http2_sessions.items():
        key_elem = key.split("|")
        http2 = {
            "http2_session_id": int(key_elem[0])
        }
        original_data = {}
        for event in values:
            if 'HTTP2_SESSION_INITIALIZED' == event.event_type and 'PHASE_NONE' in event.phase:
                dependency_socket_events = sockets.get("%s|%s" % (event.source_dependency_id, event.source_dependency_type), [])
                for s_event in dependency_socket_events:
                    if 'TCP_CONNECT' == s_event.event_type and 'PHASE_BEGIN' in s_event.phase and original_data.get('http2_conn_establish_begin') is None:
                        original_data['http2_conn_establish_begin'] = s_event.time_int
                    if 'SSL_CONNECT' == s_event.event_type and 'PHASE_END' in s_event.phase and original_data.get('http2_conn_establish_end') is None:
                        original_data['http2_conn_establish_end'] = s_event.time_int
                original_data['http2_conn_download_begin'] = event.time_int
            if 'HTTP2_SESSION_SEND_HEADERS' == event.event_type and 'PHASE_NONE' == event.phase:
                original_data['http_job_stream_id'] = event.source_dependency_id
            original_data['http2_conn_download_end'] = event.time_int
        http2['http2_session_duration'] = original_data.get('http2_conn_establish_end', 0) - original_data.get('http2_conn_establish_begin', 0) + \
                                          original_data.get('http2_conn_download_end', 0) - original_data.get('http2_conn_download_begin', 0)
        http2['http_job_stream_id'] = original_data['http_job_stream_id']
        http2['original_data'] = original_data
        http2s.append(http2)
    return http2s
