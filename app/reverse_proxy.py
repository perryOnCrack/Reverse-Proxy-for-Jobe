import os
import sys
import json
import time
from flask import Flask, jsonify
import requests

# Some constants
PATH_working_server = 'working_server.json'
PATH_joeb_list = 'jobe_list.json'
PATH_sorted_lang = 'sorted_lang.json'
TTL_working_server = 10 # Time Before Expired
TTL_jobe = 3

app = Flask(__name__)


#
# Returns a json containing supporting languages
# Somthing like this:
# [["cpp", "7.4.0"], ["python3", "3.6.5"]]
#
@app.route('/languages')
def languages():
    # Check working_server.json's mod time to determent 
    # if we need to generate new one or using existing sorted_lang.json.
    # If the file is not there, generate new one.
    if os.path.exists(PATH_working_server) and ((time.time() - os.path.getmtime(PATH_working_server)) < TTL_working_server):
        print('INFO: Using existing sorted_lang.json...')
        try:
            with open(PATH_sorted_lang, 'r') as f:
                return jsonify(json.loads(f.read()))
        except:
            print('ERROR: Failed reading "' + PATH_working_server + '"')
    
    # Generate new working_server.json.
    # Return empty if any thing goes wrong from this point forward
    # First we read in jobe_list.json
    print('INFO: Generating new working_server.json and sorted_lang.json...')
    jobe_list = ''
    try:
        with open(PATH_joeb_list, 'r') as f:
            jobe_list = json.loads(f.read())
    except:
        print('ERROR: Failed reading "' + PATH_joeb_list + '"')
        return jsonify('[]')
    # Then we request each and every server one the list.
    working_server = dict()
    for server in jobe_list['jobe']:
        r = None
        lang_list = None
        for i in range(3):
            try:
                r = requests.get(server + '/jobe/index.php/restapi/languages', timeout =TTL_jobe)
                r.raise_for_status()
                break
            except requests.exceptions.HTTPError:
                print('ERROR: ' + server + ' reposnse with ' + str(r.status_code))
                continue
            except:
                print('ERROR: Error when requesting from ' + server)
                continue
        try:
            lang_list = r.json()
        except ValueError:
            print('ERROR: error decoding json')
            continue
        # We succsessfully retrived a language list at this point.
        # Now we concider this server is in working state, so we add it to the
        # list along with its languages list.
        working_server[server] = lang_list
    try:
        with open(PATH_working_server, 'w') as f:
            f.write(json.dumps(working_server))
    except:
        print('ERROR: Failed writing ' + PATH_working_server)

    # Compose reponse data from working_server
    sorted_lang_dict = dict()
    for server in working_server:
        for lang in working_server[server]:
            if lang[0] not in sorted_lang_dict:
                sorted_lang_dict[lang[0]] = [lang[1]]
            else:
                sorted_lang_dict[lang[0]].append(lang[1])
    sorted_lang_list = list()
    for lang in sorted_lang_dict:
        tmp_list = [lang]
        for version in sorted_lang_dict[lang]:
            tmp_list.append(version)
        sorted_lang_list.append(tmp_list)
    try:
        with open(PATH_sorted_lang, 'w') as f:
            f.write(json.dumps(sorted_lang_list))
    except:
        print('ERROR: Failed writing ' + PATH_sorted_lang)

    return jsonify(sorted_lang_list)


if __name__ == '__main__':
    app.run()
