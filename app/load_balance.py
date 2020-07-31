import random

def lb_random(working_server: dict, lang_id: str):
    server_del_list = list()
    for server in working_server:
        if lang_id not in working_server[server]:
            server_del_list.append(server)

    for server in server_del_list:
        working_server.pop(server, None)

    return random.choice(list(working_server))
    

def lb_round_robin():
    pass
