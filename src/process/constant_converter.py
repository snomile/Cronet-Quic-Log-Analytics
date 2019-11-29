

event_type_dict = {}
source_type_dict = {}
phase_type_dict = {}

def revert_key_value(dict):
    return {v : k for k, v in dict.items()}

def init(constants_dict):
    global event_type_dict,source_type_dict,phase_type_dict
    event_type_dict = revert_key_value(constants_dict['logEventTypes'])
    source_type_dict = revert_key_value(constants_dict['logSourceType'])
    phase_type_dict = revert_key_value(constants_dict['logEventPhase'])

def get_event_type(type_id):
    if event_type_dict:
        return event_type_dict[type_id]
    else:
        return type_id

def get_source_type(type_id):
    if source_type_dict:
        return source_type_dict[type_id]
    else:
        return type_id

def get_phase(phase_id):
    if phase_type_dict:
        return phase_type_dict[phase_id]
    else:
        return phase_id