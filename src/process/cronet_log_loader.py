import json
import os

from collections import OrderedDict

from process import constant_converter, probe_common, probe_quic, probe_http2
from process.netlog_event import NetlogEvent


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
    transport_connect_jobs = {}
    host_resolver_impl_jobs = {}
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
        elif "TRANSPORT_CONNECT_JOB" in event_key:
            transport_connect_jobs[event_key] = value
        elif "HOST_RESOLVER_IMPL_JOB" in event_key:
            host_resolver_impl_jobs[event_key] = value
    return url_requests, http_stream_job_controllers, http_stream_jobs, quic_sessions, http2_sessions, http_sessions, \
           sockets, transport_connect_jobs, host_resolver_impl_jobs, net_log_events.values()


def process_logs_before_download(socket_values, trans_conn_values, host_resolver_values):
    sockets = probe_common.process_socket(socket_values)
    trans_conns = probe_common.process_transport_connect_job(trans_conn_values)
    host_resolver_impl_jobs = probe_common.process_host_resolver_impl_job(host_resolver_values)

    return {
        "sockets": list(filter(lambda x: int(x['http_stream_job_id']) > 0, sockets)),
        "trans_conns": list(filter(lambda x: int(x['host_resolver_impl_job_id']) > 0, trans_conns)),
        "host_resolver_impl_jobs": host_resolver_impl_jobs
    }


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


def gen_general_infos(url_requests, http_stream_job_controllers, http_stream_jobs, quic_sessions, http2_sessions, logs_before_downloads):
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
            gen_general_info.update(logs_before_downloads)
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
        if general_info.get('quic_probe'):
            probe_session_starttime = general_info['quic_probe']['quic_session_starttime']
        elif general_info['http_stream_job'].get('http2_session'):
            probe_session_starttime = general_info['http_stream_job']['http2_session']['original_data']['http2_conn_download_begin']
        else:
            probe_session_starttime = 0
        general_info_file_path = '%s%s_%s_general_info.json' % (data_converted_path, host, probe_session_starttime)
        with open(general_info_file_path, "w") as gen_f:
            json.dump(general_info, gen_f)
        general_info_files.append(general_info_file_path)
        print("generate general_info file [%s]" % general_info_file_path)
    return general_infos


def process_netlog(fullpath, project_root, data_converted_path, filename_without_ext):
    print('begin to process log file')
    log_events = parse_netlog(fullpath, project_root)
    formed_log_events = get_formed_log_events(log_events)
    url_requests = probe_common.process_events(formed_log_events[0],probe_common.process_url_request)
    http_stream_job_controllers = probe_common.process_events(formed_log_events[1],probe_common.process_http_stream_job_controller)
    http_stream_jobs = process_http_stream_job(formed_log_events[2])
    logs_before_downloads = process_logs_before_download(formed_log_events[6], formed_log_events[7], formed_log_events[8])
    quic_sessions = probe_quic.process_quic_session(formed_log_events[3], data_converted_path)
    http2_sessions = probe_http2.process_http2_session(formed_log_events[4], formed_log_events[6])
    general_infos = gen_general_infos(url_requests, http_stream_job_controllers, http_stream_jobs, quic_sessions, http2_sessions, logs_before_downloads)
    general_info_files = generate_general_info_files(general_infos, data_converted_path)
    json_files = process_probe_data(data_converted_path, filename_without_ext, formed_log_events[-1], general_infos)
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


def process_probe_data(data_converted_path, filename_without_ext, log_events, general_infos):
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
