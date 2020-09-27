def process_events(formed_elem, process_func):
    processed_data_list = []
    for key, values in formed_elem.items():
        key_elem = key.split("|")
        processed_data_list.append(process_func(key_elem[0], values))
    return processed_data_list


def process_url_request(key, events):
    url_request = {
        "url_request_id": int(key),
    }
    original_data = {}
    for event in events:
        if original_data.get('probe_start_time_int') is None:
            original_data['probe_start_time_int'] = event.time_int
        if 'URL_REQUEST_START_JOB' == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get('url_request_start_job_time_int') is None:
            original_data['url_request_start_job_time_int'] = event.time_int
        if "HTTP_STREAM_REQUEST" == event.event_type and 'PHASE_END' == event.phase and original_data.get('first_http_stream_request_end_time_int') is None:
            original_data['first_http_stream_request_end_time_int'] = event.time_int
        if "HTTP_STREAM_REQUEST" == event.event_type and 'PHASE_BEGIN' == event.phase:
            original_data['last_http_stream_request_begin_time_int'] = event.time_int
        if "HTTP_TRANSACTION_SEND_REQUEST" == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get('first_http_transaction_send_request_begin_time_int') is None:
            original_data['first_http_transaction_send_request_begin_time_int'] = event.time_int
        if "HTTP_TRANSACTION_READ_HEADERS" == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get('first_http_transaction_read_headers_begin_time_int') is None:
            original_data['first_http_transaction_read_headers_begin_time_int'] = event.time_int
        if "HTTP_TRANSACTION_READ_RESPONSE_HEADERS" == event.event_type and 'PHASE_NONE' == event.phase and original_data.get('first_http_transaction_read_response_headers_protocol') is None:
            original_data['first_http_transaction_read_response_headers_protocol'] = event.other_data['params']['headers'][0]
        if "REQUEST_ALIVE" == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get('probe_url') is None:
            original_data['probe_url'] = event.other_data['params']['url']
        original_data['probe_end_time_int'] = event.time_int
    url_request['probe_start_delayed_duration'] = original_data.get('url_request_start_job_time_int', -1) - original_data.get('probe_start_time_int', -1)
    url_request['conn_establish_duration'] = original_data.get('last_http_stream_request_begin_time_int', -1) - original_data.get('url_request_start_job_time_int', -1)
    url_request['probe_request_start_offset'] = original_data.get('first_http_transaction_send_request_begin_time_int', -1) - original_data.get('url_request_start_job_time_int', -1)
    url_request['first_pkg_offset'] = original_data.get('first_http_transaction_read_headers_begin_time_int', -1) - original_data.get('url_request_start_job_time_int', -1)
    url_request['first_pkg_status'] = int(original_data.get('first_http_transaction_read_response_headers_protocol').split(" ")[1]) if "HTTP" in original_data.get('first_http_transaction_read_response_headers_protocol', "NULL") else -1
    url_request['probe_duration'] = original_data['probe_end_time_int'] - original_data.get('url_request_start_job_time_int', -1)
    url_request['probe_url'] = original_data['probe_url']
    url_request['original_data'] = original_data
    return url_request


def process_http_stream_job_controller(key, events):
    http_stream_job_controller = {
        "http_stream_job_controller_id": int(key)
    }
    original_data = {}
    for event in events:
        if "HTTP_STREAM_JOB_CONTROLLER_PROXY_SERVER_RESOLVED" == event.event_type and original_data.get('proxy_server') is None:
            original_data['proxy_server'] = event.other_data.get('params', {'proxy_server': "NONE"}).get('proxy_server')
        if "HTTP_STREAM_JOB_CONTROLLER_BOUND" == event.event_type and original_data.get('url_request_id') is None:
            original_data['url_request_id'] = event.source_dependency_id
        if 'HTTP_STREAM_JOB_CONTROLLER' == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get("stream_start_time_int") is None:
            original_data['stream_start_time_int'] = event.time_int
        if 'HTTP_STREAM_REQUEST_STARTED_JOB' == event.event_type and original_data.get("stream_job_start_time_int") is None:
            original_data['stream_job_start_time_int'] = event.time_int
    http_stream_job_controller['proxy_server'] = original_data.get('proxy_server', 'NONE')
    http_stream_job_controller['url_request_id'] = original_data.get('url_request_id')
    # http_stream_job_controller['stream_start_time_int'] = original_data.get('stream_start_time_int')
    # http_stream_job_controller['stream_job_start_time_int'] = original_data.get('stream_job_start_time_int')
    http_stream_job_controller['stream_job_start_offset'] = original_data.get('stream_job_start_time_int') - original_data.get('stream_start_time_int')
    http_stream_job_controller['original_data'] = original_data
    return http_stream_job_controller


def process_transport_connect_job(resolver_jobs):
    resolvers = []
    for key, values in resolver_jobs.items():
        key_elem = key.split("|")
        resolver = {
            "transport_connect_job_id": int(key_elem[0])
        }
        original_data = {}
        for event in values:
            if "CONNECT_JOB" == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get('connect_begin') is None:
                original_data['connect_begin'] = event.time_int
            if "HOST_RESOLVER_IMPL_JOB_ATTACH" == event.event_type and original_data.get('host_resolver_begin') is None:
                original_data['host_resolver_begin'] = event.time_int
            if "HOST_RESOLVER_IMPL_JOB_ATTACH" == event.event_type and original_data.get('host_resolver_impl_job_id') is None:
                original_data['host_resolver_impl_job_id'] = event.source_dependency_id
            resolver['host_resolver_impl_job_id'] = original_data.get('host_resolver_impl_job_id', -1)
            resolver['before_dns_duration'] = original_data.get('host_resolver_begin', 0) - original_data.get('connect_begin', 0)
            resolver['original_data'] = original_data
        resolvers.append(resolver)
    return resolvers


def process_socket(resolver_jobs):
    resolvers = []
    for key, values in resolver_jobs.items():
        key_elem = key.split("|")
        resolver = {
            "socket_id": int(key_elem[0])
        }
        original_data = {}
        for event in values:
            if "TCP_CONNECT" == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get('tcp_conn_begin') is None:
                original_data['tcp_conn_begin'] = event.time_int
            if "TCP_CONNECT" == event.event_type and 'PHASE_END' == event.phase and original_data.get('tcp_conn_end') is None:
                original_data['tcp_conn_end'] = event.time_int
            if "SOCKET_ALIVE" == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get('transport_connect_job_id') is None:
                original_data['transport_connect_job_id'] = event.source_dependency_id
            if "SOCKET_IN_USE" == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get('http_stream_job_id') is None:
                original_data['http_stream_job_id'] = event.source_dependency_id
            resolver['http_stream_job_id'] = original_data.get('http_stream_job_id', -1)
            resolver['transport_connect_job_id'] = original_data.get('transport_connect_job_id', -1)
            resolver['tcp_conn_duration'] = original_data.get('tcp_conn_end', 0) - original_data.get('tcp_conn_begin', 0)
            resolver['original_data'] = original_data
        resolvers.append(resolver)
    return resolvers


def process_host_resolver_impl_job(resolver_jobs):
    resolvers = []
    for key, values in resolver_jobs.items():
        key_elem = key.split("|")
        resolver = {
            "host_resolver_impl_job_id": int(key_elem[0])
        }
        original_data = {}
        for event in values:
            if "HOST_RESOLVER_IMPL_JOB" == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get('host') is None:
                original_data['host'] = event.other_data.get('params', {'host': "NONE"}).get('host')
            if "HOST_RESOLVER_IMPL_JOB" == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get('dns_begin_time') is None:
                original_data['dns_begin_time'] = event.time_int
            if "HOST_RESOLVER_IMPL_JOB" == event.event_type and 'PHASE_END' == event.phase and original_data.get('dns_end_time') is None:
                original_data['dns_end_time'] = event.time_int
            resolver['host'] = original_data.get('host', "host")
            resolver['dns_begin_time'] = original_data.get('dns_begin_time', 0)
            resolver['dns_duration'] = original_data.get('dns_end_time', 0) - original_data.get('dns_begin_time', 0)
            resolver['original_data'] = original_data
        resolvers.append(resolver)
    return resolvers
