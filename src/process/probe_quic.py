import csv
from process.quic_connection import QuicConnection


def process_quic_session(quic_formed_elem, data_converted_path):
    quics = []
    for key, values in quic_formed_elem.items():
        key_elem = key.split("|")
        quic = {
            "quic_session_id": int(key_elem[0])
        }
        host = "host"
        dns_begin_time = 0
        dns_end_time = 0
        for event in values:
            if 'QUIC_SESSION' == event.event_type and 'PHASE_BEGIN' in event.phase:
                host = event.other_data.get('params').get('host')
        quic_connection = QuicConnection(host, dns_begin_time, dns_end_time, values, data_converted_path, "")
        json_obj = quic_connection.save()
        quic['original_datas'] = json_obj.get('general_info')
        quic['full_path_json_file'] = json_obj.get('fullpath_json_file')
        quic['quic_session_starttime'] = values[0].time_int
        quics.append(quic)
    return quics


def persist_event_list_to_csv(data_converted_path, filename_without_ext, event_list):
    with open(data_converted_path + filename_without_ext + '.csv', 'wt') as f:
        cw = csv.writer(f)
        cw.writerow(['time', 'time_elaps','event_type','source_id','source_type','phase','source_dependency_id','source_dependency_type','other_data'])
        for c_event in event_list:
            for event in c_event:
                cw.writerow(event.get_info_list())
