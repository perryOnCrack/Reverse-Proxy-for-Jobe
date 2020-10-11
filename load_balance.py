import random

def lb_random(working_server: dict, lang_id: str):
    if lang_id == '__weight':
        return 'Nope'

    # Delete every server that doesn't support the language(lang_id)
    # Pop the list of servers to be excluded
    for server in [server for server in working_server if lang_id not in working_server[server]]:
        working_server.pop(server, None)

    # [working_server[server]['__weight'] for server in working_server] pulls out the weight value as a list
    # (List comprehension is fun lol)
    return random.choices(list(working_server), [working_server[server]['__weight'] for server in working_server])[0]
    

def lb_round_robin():
    pass
