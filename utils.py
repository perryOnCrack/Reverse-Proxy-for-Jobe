import requests, json
import global_vars

def list_of_list_to_dict(input_list):
    ret = dict()
    for pair in input_list:
        ret[pair[0]] = pair[1]
    return ret

def send_run_to_jobe(jobe_url, request_data):
    success = False
    error_string = None
    error_code = None
    reponse_data = None

    try:
        r = None
        r = requests.post(jobe_url + '/jobe/index.php/restapi/runs', json = request_data, timeout = global_vars.TTL_jobe_submit_runs)
        r.raise_for_status()
        # Success with result
        success = True
        reponse_data = r.json()
    # All other error
    except requests.Timeout:
        error_string = 'timeout'
        error_code = -1
    except requests.ConnectionError: # No connection between jobe and this proxy
        error_string = 'no_connection'
        error_code = -2
    except:
        error_string = 'other_error'
        error_code = r.status_code

    return [success, reponse_data, error_code, error_string]



def send_file_to_jobe(jobe_url, file_list):
    success = False
    error_string = None
    error_code = None

    for file_pair in file_list:
        try:
            r = None
            with open(global_vars.PATH_PREFIX_file_cache + file_pair[0], 'r') as f:
                r = requests.put(jobe_url + '/jobe/index.php/restapi/files/' + file_pair[0], json = json.loads(f.read()))
            r.raise_for_status()
        # All other error
        except requests.Timeout:
            error_string = 'timeout'
            error_code = -1
            break
        except requests.ConnectionError: # No connection between jobe and this proxy
            error_string = 'no_connection'
            error_code = -2
            break
        except:
            error_string = 'other_error'
            error_code = r.status_code
            break
    
    # Success with result
    success = True
    
    return [success, error_code, error_string]
