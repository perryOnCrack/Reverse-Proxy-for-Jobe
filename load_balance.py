import random

def lb_random(working_server: dict, lang_id: str):
    if lang_id == '__weight':
        return 'Nope'

    # [working_server[server]['__weight'] for server in working_server] pulls out the weight value as a list
    # (List comprehension is fun lol)
    return random.choices(list(working_server), [working_server[server]['__weight'] for server in working_server])[0]
    

def lb_round_robin():
    pass
