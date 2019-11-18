

event_type_dict = {}
source_type_dict = {}

def revert_key_value(dict):
    return {v : k for k, v in dict.items()}

def init(constants_dict):
    global event_type_dict,source_type_dict
    event_type_dict = revert_key_value(constants_dict['logEventTypes'])
    source_type_dict = revert_key_value(constants_dict['logSourceType'])

def get_event_type(type_id):
    return event_type_dict[type_id]

def get_source_type(type_id):
    return source_type_dict[type_id]