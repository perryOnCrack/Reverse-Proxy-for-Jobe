def list_of_list_to_dict(input_list):
    ret = dict()
    for pair in input_list:
        ret[pair[0]] = pair[1]
    return ret
