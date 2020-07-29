import os, sys, json, time, base64
from flask import Flask, jsonify, request
import requests

#======================================================
# Some parameters
#======================================================
# File path to resourses
PATH_working_server = 'working_server.json'
PATH_joeb_list = 'jobe_list.json'
PATH_sorted_lang = 'sorted_lang.json'
PATH_PREFIX_file_cache = 'file_cache/'

TTL_working_server = 10 # working_server.json's expire time, in sec
TTL_jobe_request = 3 # request timeout on every jobe server, in sec


app = Flask(__name__)


#======================================================
# API call: get_languages
#
# Returns a json containing supporting languages
# Something like this:
# [["cpp", "7.4.0"], ["python3", "3.6.5"]]
# 
# Returns:
#  200 on success
#  400 on on illegal request parameters
#   (but when will that ever happened?)
#======================================================
@app.route('/languages', methods = ['GET'])
def get_languages():
    # Check working_server.json and sorted_lang.json's modification time to determent if we need to generate new ones or using existing ones.
    # If the either one of the files does not exsist, generate new ones.
    if os.path.exists(PATH_working_server) and ((time.time() - os.path.getmtime(PATH_working_server)) < TTL_working_server) and \
        os.path.exists(PATH_sorted_lang) and ((time.time() - os.path.getmtime(PATH_sorted_lang)) < TTL_working_server):
        print('INFO: Using existing sorted_lang.json...')
        try:
            with open(PATH_sorted_lang, 'r') as f:
                return jsonify(json.loads(f.read())), 200
        except:
            print('ERROR: Failed reading "' + PATH_sorted_lang + '"')
    
    # Generate new working_server.json.
    # First we read in jobe_list.json
    print('INFO: Generating new working_server.json and sorted_lang.json...')
    jobe_list = ''
    try:
        with open(PATH_joeb_list, 'r') as f:
            jobe_list = json.loads(f.read())
    except:
        print('ERROR: Failed reading "' + PATH_joeb_list + '"')
        return jsonify([]), 200
    # Then we request each and every server one the list.
    working_server = dict()
    for server in jobe_list['jobe']:
        r = None
        lang_list = None
        for i in range(3): # try 3 times before moving on.
            try:
                r = requests.get(server['url'] + '/jobe/index.php/restapi/languages', timeout =TTL_jobe_request)
                r.raise_for_status()
                lang_list = r.json()
                working_server[server['url']] = lang_list
                break
            except requests.exceptions.HTTPError: # anything other than respond code 200
                print('ERROR: ' + server['url'] + ' reposnse with ' + str(r.status_code))
            except ValueError: # it's for r.json()
                print('ERROR: error decoding json')
            except:
                print('ERROR: Error when requesting from ' + server['url'])
    
    # Save to working_server.json.
    try:
        with open(PATH_working_server, 'w') as f:
            f.write(json.dumps(working_server))
    except:
        print('ERROR: Failed writing ' + PATH_working_server)
        return jsonify([]), 200

    # Compose reponse data from working_server
    # TODO: Combine the 2 nested loops.
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
    
    # Save to sorted_lang.json
    try:
        with open(PATH_sorted_lang, 'w') as f:
            f.write(json.dumps(sorted_lang_list))
    except:
        print('ERROR: Failed writing ' + PATH_sorted_lang)
        return jsonify([]), 200

    return jsonify(sorted_lang_list), 200


#======================================================
# API call: put_file
#
# Like the name sugguests, it put files in the server 
# via PUT request in parameter file_contents.
# 
# It save the file to this proxy instead of the actual 
# jobe server until submit_run is called.
#
# It won't decode the base64 content sent to this proxy 
# since the file content is non of its business and we 
# can save some cpu cycles by not doing it.
# 
# Returns:
#  204 on success
#  400 on contents are not a valid base-64 encoding
#  403 if the server does not trust the client to
#   provide a unique file ID
#   - NOT impelemented atm.
#======================================================
@app.route('/files/<file_uid>', methods = ['PUT'])
def put_file(file_uid):
    # Code for decode base64
    #f.write(base64.b64decode(data['file_contents']))

    # Check if the file exist or not
    if os.path.exists(PATH_PREFIX_file_cache + file_uid):
        # To save cpu cycle, we just ignore it if it exist.
        return '', 204
    else:
        try:
            data = request.get_data()
            with open('file_cache/' + file_uid, 'wb') as f:
                f.write(data)
            return '', 204
        except:
            return '', 400

#======================================================
# API call: check_file
#
# Like the name sugguests, it checks cached files in 
# the server via HEAD request.
# 
# It checks if the file is present in this proxy 
# instead of the actual jobe server.
#
# Returns:
#  204 on success
#  400 on illegal parameter
#  404 on file not found
#======================================================
@app.route('/files/<file_uid>', methods = ['HEAD'])
def check_file(file_uid):
    # Check if the file exist or not
    if os.path.exists(PATH_PREFIX_file_cache + file_uid):
        # To save cpu cycle, we just ignore it if it exist.
        return '', 204
    else:
        return '', 404
    return '', 400


#======================================================
# API call: submit_run
#
# The elephant in the room. It check if the file needed
# is in this proxy, then decide which jobe server to
# sned to and retrive and return result back to client.
# 
# Returns:
# 200 when the runs is sucessful and with result
# 202 when the run is pending on jobe
#  - which is impossible because jobe server only runs
#  in immediate mode right now
# 400 on illegal parameter
# 404 when file needed is not found on the proxy
#======================================================
@app.route('/runs', methods = ['POST'])
def submit_runs():
    return '', 404


#======================================================
# API call: post_file
#
# Like the name sugguests, it put files in the server 
# via POST request in parameter file_contents.
# 
# It save the file to this proxy instead of the actual 
# jobe server until submit_run is called.
#
# Hmmm, it isn't implemented by jobe yet. Returns 403
# in current state.
# 
# Returns:
# ====ONLY RESPONSES 403 IN CURRENT STATE====
#  200 on success
#  400 on contents are not a valid base-64 encoding
#======================================================
@app.route('/files', methods = ['POST'])
def post_file():
    return '', 403


#======================================================
# API call: get_run_status
#
# Like the name sugguests, it gets status of a 
# pending run.
#
# It's not being implemented by jobe right now.
# Only Returns 404 in current state.
# 
# Returns:
# ====ONLY RESPONSES 404 IN CURRENT STATE====
#======================================================
@app.route('/runresults/id', methods = ['GET'])
def get_run_status():
    return '', 404

if __name__ == '__main__':
    app.run()
