import json
import os

from collections import OrderedDict

from process import constant_converter, probe_common, probe_quic, probe_http2
from process.netlog_event import NetlogEvent
# from process.quic_session import QuicSession, ClientQuicSession, ServerQuicSession
# from process.quic_connection import QuicConnection


def get_formed_log_events(log_events):
    net_log_events = OrderedDict()
    for log_event in log_events:
        net_log_event = NetlogEvent(log_event)
        nles_key = "%s|%s" % (net_log_event.source_id, net_log_event.source_type)
        if net_log_events.get(nles_key) is None:
            net_log_events[nles_key] = [net_log_event]
        else:
            net_log_events[nles_key].append(net_log_event)
    url_requests = {}
    http_stream_job_controllers = {}
    http_stream_jobs = {}
    quic_sessions = {}
    http2_sessions = {}
    http_sessions = {}
    sockets = {}
    for event_key, value in net_log_events.items():
        if "URL_REQUEST" in event_key:
            url_requests[event_key] = value
        elif "HTTP_STREAM_JOB_CONTROLLER" in event_key:
            http_stream_job_controllers[event_key] = value
        elif "HTTP_STREAM_JOB" in event_key:
            http_stream_jobs[event_key] = value
        elif "QUIC_SESSION" in event_key:
            quic_sessions[event_key] = value
        elif "HTTP2_SESSION" in event_key:
            http2_sessions[event_key] = value
        elif "HTTP_SESSION" in event_key:
            http_sessions[event_key] = value
        elif "|SOCKET" in event_key:
            sockets[event_key] = value
    return url_requests, http_stream_job_controllers, http_stream_jobs, quic_sessions, http2_sessions, http_sessions, sockets, net_log_events.values()


def process_url_request(formed_elem):
    url_requests = []
    for key, values in formed_elem.items():
        key_elem = key.split("|")
        url_request = {
            "url_request_id": int(key_elem[0]),
        }
        original_data = {}
        for event in values:
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
        # url_request['conn_establish_duration'] = abs(original_data.get('last_http_stream_request_begin_time_int', -1) - original_data.get('first_http_stream_request_end_time_int', -1))
        # url_request['probe_request_start_offset'] = original_data.get('first_http_transaction_send_request_begin_time_int', -1) - original_data.get('probe_start_time_int', -1)
        # url_request['first_pkg_offset'] = original_data.get('first_http_transaction_read_headers_begin_time_int', -1)- original_data.get('probe_start_time_int', -1)
        # url_request['first_pkg_status'] = original_data.get('first_http_transaction_read_response_headers_protocol').split(" ")[1] if "HTTP" in original_data.get('first_http_transaction_read_response_headers_protocol', "NULL") else -1
        # url_request['probe_start_delayed_duration'] = original_data.get('url_request_start_job_time_int', -1) - original_data.get('probe_start_time_int', -1)
        url_request['probe_start_delayed_duration'] = original_data.get('url_request_start_job_time_int', -1) - original_data.get('probe_start_time_int', -1)
        url_request['conn_establish_duration'] = original_data.get('last_http_stream_request_begin_time_int', -1) - original_data.get('url_request_start_job_time_int', -1)
        url_request['probe_request_start_offset'] = original_data.get('first_http_transaction_send_request_begin_time_int', -1) - original_data.get('url_request_start_job_time_int', -1)
        url_request['first_pkg_offset'] = original_data.get('first_http_transaction_read_headers_begin_time_int', -1) - original_data.get('url_request_start_job_time_int', -1)
        url_request['first_pkg_status'] = int(original_data.get('first_http_transaction_read_response_headers_protocol').split(" ")[1]) if "HTTP" in original_data.get('first_http_transaction_read_response_headers_protocol', "NULL") else -1
        url_request['probe_duration'] = original_data['probe_end_time_int'] - original_data.get('url_request_start_job_time_int', -1)
        url_request['probe_url'] = original_data['probe_url']
        url_request['original_data'] = original_data
        url_requests.append(url_request)
    return url_requests


def process_http_stream_job_controller(formed_elem):
    http_stream_job_controllers = []
    for key, values in formed_elem.items():
        key_elem = key.split("|")
        http_stream_job_controller = {
            "http_stream_job_controller_id": int(key_elem[0])
        }
        original_data = {}
        for event in values:
            if "HTTP_STREAM_JOB_CONTROLLER_PROXY_SERVER_RESOLVED" == event.event_type and original_data.get('proxy_server') is None:
                original_data['proxy_server'] = event.other_data.get('params', {'proxy_server': "NONE"}).get('proxy_server')
            if "HTTP_STREAM_JOB_CONTROLLER_BOUND" == event.event_type and original_data.get('url_request_id') is None:
                original_data['url_request_id'] = event.source_dependency_id
            if 'HTTP_STREAM_JOB_CONTROLLER' == event.event_type and 'PHASE_BEGIN' == event.phase and original_data.get("stream_start_time_int") is None:
                original_data['stream_start_time_int'] = event.time_int
        http_stream_job_controller['proxy_server'] = original_data.get('proxy_server', 'NONE')
        http_stream_job_controller['url_request_id'] = original_data.get('url_request_id')
        http_stream_job_controller['stream_start_time_int'] = original_data.get('stream_start_time_int')
        http_stream_job_controller['original_data'] = original_data
        http_stream_job_controllers.append(http_stream_job_controller)
    return http_stream_job_controllers


def process_http_stream_job(formed_elem):
    http_stream_jobs = []
    original_datas = {}
    for key, values in formed_elem.items():
        key_elem = key.split("|")
        http_stream_job_controller_id = -1
        for event in values:
            if 'HTTP_STREAM_JOB' == event.event_type and 'PHASE_BEGIN' in event.phase:
                http_stream_job_controller_id = event.source_dependency_id
                probe_url = event.other_data.get('params', {'original_url': 'NONE'}).get('original_url')
                http_job_count = 1 if 'http://' in probe_url else 0
                if original_datas.get(http_stream_job_controller_id) is None:
                    original_datas[event.source_dependency_id] = {
                        'probe_url': probe_url,
                        'using_quic': event.other_data.get('params', {'using_quic': False}).get('using_quic'),
                        'stream_jobs': [int(key_elem[0])],
                        'http_job_counts': http_job_count,
                        'http2_job_counts': 0,
                        # 'quic_job_counts': 0
                    }
                else:
                    old_using_quic = original_datas.get(http_stream_job_controller_id).get('using_quic')
                    new_using_quic = event.other_data.get('params', {'using_quic': False}).get('using_quic')
                    original_datas.get(http_stream_job_controller_id)['using_quic'] = old_using_quic or new_using_quic
                    original_datas.get(http_stream_job_controller_id)['stream_jobs'].append(int(key_elem[0]))
                    original_datas.get(http_stream_job_controller_id)['http_job_counts'] = original_datas.get(http_stream_job_controller_id).get('http_job_counts') + http_job_count
            # if 'HTTP_STREAM_JOB_BOUND_TO_QUIC_STREAM_FACTORY_JOB' == event.event_type:
            #     original_datas.get(http_stream_job_controller_id)['quic_job_counts'] = original_datas.get(http_stream_job_controller_id).get('quic_job_counts') + 1
            if 'HTTP2_SESSION_POOL_IMPORTED_SESSION_FROM_SOCKET' == event.event_type:
                original_datas.get(http_stream_job_controller_id)['http2_job_counts'] = original_datas.get(http_stream_job_controller_id).get('http2_job_counts') + 1
    for key, values in original_datas.items():
        http_stream_job = {
            "http_stream_job_controller_id": key
        }
        http_stream_job['original_data'] = values
        probe_url = http_stream_job['original_data']['probe_url']
        if "https://" in probe_url:
            if http_stream_job['original_data']['using_quic']:
                http_stream_job['probe_protocol'] = "quic"
            else:
                http_stream_job['probe_protocol'] = "http2"
        elif "http://" in probe_url:
            http_stream_job['probe_protocol'] = "http"
        else:
            http_stream_job['probe_protocol'] = "others"
        http_stream_job['probe_url'] = probe_url[probe_url.index("://") + 3: -1]
        http_stream_job['stream_job_counts'] = len(http_stream_job['original_data']['stream_jobs'])
        http_stream_job['http_job_counts'] = http_stream_job['original_data']['http_job_counts']
        http_stream_job['http2_job_counts'] = http_stream_job['original_data']['http2_job_counts']
        # http_stream_job['quic_job_counts'] = http_stream_job['original_data']['quic_job_counts']
        http_stream_jobs.append(http_stream_job)
    return http_stream_jobs


def gen_general_infos(url_requests, http_stream_job_controllers, http_stream_jobs, quic_sessions, http2_sessions):
    # http2_session_durations = []
    if len(url_requests) == 0 and len(quic_sessions) > 0:
        return [{
            'http_stream_job': {'probe_url': quic_session['original_datas']['host']},
            'http_stream_job_controller': {'stream_start_time_int': quic_session['quic_session_starttime']},
            'quic_probe': quic_session
        } for quic_session in quic_sessions]
    else:
        gen_general_infos = {}
        for stream_job_controller_elem in http_stream_job_controllers:
            gen_general_info = {}
            url_request_id = stream_job_controller_elem.get('url_request_id', -1)
            filtered_url_requests = [x for x in url_requests if x.get('url_request_id', -1) == url_request_id]
            gen_general_info['url_request'] = filtered_url_requests[0]
            gen_general_info['http_stream_job_controller'] = stream_job_controller_elem
            gen_general_info['url_request']['http_stream_job_controller_counts'] = 1
            gen_general_infos[stream_job_controller_elem.get('http_stream_job_controller_id')] = gen_general_info
        for stream_job_elem in http_stream_jobs:
            for http2_session in http2_sessions:
                if http2_session.get('http_job_stream_id', -2) in stream_job_elem.get('original_data', {'stream_jobs': [-1]}).get('stream_jobs'):
                    stream_job_elem['http2_session'] = http2_session
                    # http2_session_durations.append(http2_session['http2_session_duration'])
            gen_general_infos[stream_job_elem.get('http_stream_job_controller_id', -1)]['http_stream_job'] = stream_job_elem
        gen_general_info_keys = sorted(gen_general_infos.keys())
        for quic_session in quic_sessions:
            last_key = 0
            for gg_key in gen_general_info_keys:
                if gg_key > quic_session['quic_session_id']:
                    gen_general_infos[last_key]['http_stream_job']["quic_job_counts"] = gen_general_infos[last_key]['http_stream_job'].get("quic_job_counts", 0) + 1
                    gen_general_infos[last_key]['quic_probe'] = quic_session
                    last_key = gg_key
                    break
                last_key = gg_key
            if quic_session['quic_session_id'] > last_key:
                gen_general_infos[last_key]['http_stream_job']["quic_job_counts"] = gen_general_infos[last_key]['http_stream_job'].get("quic_job_counts", 0) + 1
                gen_general_infos[last_key]['quic_probe'] = quic_session
            # return gen_general_infos.values(), http2_session_durations
        return gen_general_infos.values()


def generate_general_info_files(general_infos, data_converted_path):
    general_info_files = []
    for general_info in general_infos:
        host = general_info['http_stream_job']['probe_url']
        probe_session_starttime = general_info['http_stream_job_controller']['stream_start_time_int']
        general_info_file_path = '%s%s_%s_general_info.json' % (data_converted_path, host, probe_session_starttime)
        with open(general_info_file_path, "w") as gen_f:
            json.dump(general_info,gen_f)
        general_info_files.append(general_info_file_path)
        print("generate general_info file [%s]" % general_info_file_path)
    return general_infos


# def process_quic_session(quic_formed_elem, data_converted_path):
#     quics = []
#     for key, values in quic_formed_elem.items():
#         key_elem = key.split("|")
#         quic = {
#             "quic_session_id": int(key_elem[0])
#         }
#         host = "host"
#         dns_begin_time = 0
#         dns_end_time = 0
#         for event in values:
#             if 'QUIC_SESSION' == event.event_type and 'PHASE_BEGIN' in event.phase:
#                 host = event.other_data.get('params').get('host')
#         quic_connection = QuicConnection(host, dns_begin_time, dns_end_time, values, data_converted_path, "")
#         json_obj = quic_connection.save()
#         quic['original_datas'] = json_obj.get('general_info')
#         quic['full_path_json_file'] = json_obj.get('fullpath_json_file')
#         quic['quic_session_starttime'] = values[0].time_int
#         quics.append(quic)
#     return quics


# def process_http2_session(http2_sessions, sockets):
#     http2s = []
#     for key, values in http2_sessions.items():
#         key_elem = key.split("|")
#         http2 = {
#             "http2_session_id": int(key_elem[0])
#         }
#         original_data = {}
#         for event in values:
#             if 'HTTP2_SESSION_INITIALIZED' == event.event_type and 'PHASE_NONE' in event.phase:
#                 dependency_socket_events = sockets.get("%s|%s" % (event.source_dependency_id, event.source_dependency_type), [])
#                 for s_event in dependency_socket_events:
#                     if 'TCP_CONNECT' == s_event.event_type and 'PHASE_BEGIN' in s_event.phase and original_data.get('http2_conn_establish_begin') is None:
#                         original_data['http2_conn_establish_begin'] = s_event.time_int
#                     if 'SSL_CONNECT' == s_event.event_type and 'PHASE_END' in s_event.phase and original_data.get('http2_conn_establish_end') is None:
#                         original_data['http2_conn_establish_end'] = s_event.time_int
#                 original_data['http2_conn_download_begin'] = event.time_int
#             if 'HTTP2_SESSION_SEND_HEADERS' == event.event_type and 'PHASE_NONE' == event.phase:
#                 original_data['http_job_stream_id'] = event.source_dependency_id
#             original_data['http2_conn_download_end'] = event.time_int
#         http2['http2_session_duration'] = original_data.get('http2_conn_establish_end', 0) - original_data.get('http2_conn_establish_begin', 0) + \
#                                                   original_data.get('http2_conn_download_end', 0) - original_data.get('http2_conn_download_begin', 0)
#         http2['http_job_stream_id'] = original_data['http_job_stream_id']
#         http2['original_data'] = original_data
#         http2s.append(http2)
#     return http2s


def process_netlog(fullpath, project_root, data_converted_path, filename_without_ext):
    print('begin to process log file')
    log_events = parse_netlog(fullpath, project_root)
    formed_log_events = get_formed_log_events(log_events)
    # url_requests = process_url_request(formed_log_events[0])
    # http_stream_job_controllers = process_http_stream_job_controller(formed_log_events[1])
    url_requests = probe_common.process_events(formed_log_events[0],probe_common.process_url_request)
    http_stream_job_controllers = probe_common.process_events(formed_log_events[1],probe_common.process_http_stream_job_controller)
    http_stream_jobs = process_http_stream_job(formed_log_events[2])
    # quic_sessions = process_quic_session(formed_log_events[3], data_converted_path)
    quic_sessions = probe_quic.process_quic_session(formed_log_events[3], data_converted_path)
    http2_sessions = probe_http2.process_http2_session(formed_log_events[4], formed_log_events[6])
    # general_infos, http2_session_durations = gen_general_infos(url_requests, http_stream_job_controllers, http_stream_jobs, quic_sessions, http2_sessions)
    general_infos = gen_general_infos(url_requests, http_stream_job_controllers, http_stream_jobs, quic_sessions, http2_sessions)
    # for formed_elem in formed_log_events:
    #     url_request_matrix = process_url_request(formed_elem)
    #     for req_content_elem in formed_elem['REQUEST_CONTENT']:
    #         general_info = {}
    #         general_info.update(url_request_matrix)
    #         general_info.update(process_http_stream_job_controller(req_content_elem))
    #         general_info.update(process_http_stream_job(req_content_elem))
    #         general_info.update(process_probe_data(data_converted_path, filename_without_ext, log_events))
    #         general_infos.append(general_info)
    # json_files = [x['json_file'] for x in general_infos]
    general_info_files = generate_general_info_files(general_infos, data_converted_path)
    # json_files = process_probe_data(data_converted_path, filename_without_ext, log_events, general_infos)
    json_files = process_probe_data(data_converted_path, filename_without_ext, formed_log_events[-1], general_infos)
    # json_files = []
    # print("====", http2_session_durations)
    print('log file process finished')
    return json_files


def parse_netlog(fullpath, project_root):
    # fix a not json formed file
    fix_truncated_file(fullpath)
    # load log data
    with open(fullpath, 'r') as load_f:
        load_dict = json.load(load_f)
    # convert and save chrome event log
    if 'constants' in load_dict.keys():
        constants = load_dict['constants']
    else:
        # append clipped constants
        with open(project_root + '/resource/constants/constants.json', 'r') as load_f:
            constants = json.load(load_f)['constants']
            constants['timeTickOffset'] = load_dict['timeTickOffset']
            # save to log file
            load_dict['constants'] = constants
            with open(fullpath, "w") as f:
                json.dump(load_dict, f)
    constant_converter.init(constants)
    # get log events
    log_events = load_dict['events']
    print('load', len(log_events), 'events')
    return log_events


def fix_truncated_file(file_path):
    with open(file_path, 'rb+') as load_f:
        # fix trunced file
        load_f.seek(-5, 2)
        last_char = str(load_f.read(5), encoding="utf-8").strip('\r\n')
        if last_char.endswith('],'):
            new_last_char = last_char[: last_char.index('],')] + ']}   '
            print('file trunced, fixed by appending }')
            load_f.seek(-5, 2)
            load_f.write(bytes(new_last_char, encoding="utf8"))
        elif last_char.endswith('},'):
            new_last_char = last_char[: last_char.index('},')] + '}]}   '
            print('file trunced, fixed by appending }]}')
            load_f.seek(-5, 2)
            load_f.write(bytes(new_last_char, encoding="utf8"))
        else:
            print('no need to fix')


#use first handshake message type to judge the log type
# def get_netlog_type(events):
#     for event in events:
#         if event['type'] == 268:  # "QUIC_SESSION_CRYPTO_HANDSHAKE_MESSAGE_RECEIVED":268,
#             return 'server'
#         if event['type'] == 269:  # "QUIC_SESSION_CRYPTO_HANDSHAKE_MESSAGE_SENT":269,
#             return 'client'


def process_probe_data(data_converted_path, filename_without_ext, log_events, general_infos):
    # log_type = get_netlog_type(log_events)
    # print('netlog type is', log_type)
    # start_time = int(log_events[0]['time'])
    # if log_type == 'client':
    #     quic_session = ClientQuicSession(start_time, data_converted_path, filename_without_ext)
    # else:
    #     quic_session = ServerQuicSession(start_time, data_converted_path, filename_without_ext)
    # for log_event in log_events:
    #     c_event = NetlogEvent(log_event)
    #     quic_session.add_event(c_event)
    # quic_session.save()
    # json_files = quic_session.create_quic_connection()
    probe_quic.persist_event_list_to_csv(data_converted_path, filename_without_ext, log_events)
    json_files = []
    for info in general_infos:
        if info.get('quic_probe'):
            json_files.append(info.get('quic_probe').get('full_path_json_file'))
    return json_files


if __name__ == '__main__':
    project_root = "E:/repository/git/Cronet-Quic-Log-Analytics"
    data_converted_path = "E:/repository/git/Cronet-Quic-Log-Analytics/resource/data_converted/"
    filename_without_ext = "test"
    # file_paths = ["E:/repository/git/Cronet-Quic-Log-Analytics/resource/data_original/netlog-http-1-02.json"]
    root_dir = "E:/repository/git/Cronet-Quic-Log-Analytics/resource/data_original/test"
    file_paths = os.listdir(root_dir)
    for file_path_elem in file_paths:
        file_path = os.path.join(root_dir, file_path_elem)
        print(process_netlog(file_path, project_root, data_converted_path, filename_without_ext))
