import os, sys, json, time, base64
from flask import Flask, jsonify, request
import requests
import utils, load_balance
import logging


#======================================================
# Some parameters
#======================================================
URI_prefix = '/jobe/index.php/restapi'

# File path to resourses
PATH_working_server = 'working_server.json'
PATH_joeb_list = 'jobe_list.json'
PATH_sorted_lang = 'sorted_lang.json'
PATH_PREFIX_file_cache = 'file_cache/'

# Some timeout params
TTL_working_server = 60 #180 # working_server.json's expire time (in sec.)
TTL_jobe_get_languages = 1 # request timeout on every jobe server when calling get_languages (in sec.)
TTL_jobe_submit_runs = 180 # request timeout on every jobe server when calling submit_runs (in sec.)


#======================================================
# Flask app initializtion
#======================================================
app = Flask(__name__)


#======================================================
# Let gunicotn takeover logger
#======================================================
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


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
@app.route(URI_prefix + '/languages', methods = ['GET'])
def get_languages():
    # Check working_server.json and sorted_lang.json's modification time to determent 
    # if we need to generate new ones or using existing ones.
    # If the either one of the files does not exsist, generate new ones.
    if os.path.exists(PATH_working_server) and ((time.time() - os.path.getmtime(PATH_working_server)) < TTL_working_server) and \
        os.path.exists(PATH_sorted_lang) and ((time.time() - os.path.getmtime(PATH_sorted_lang)) < TTL_working_server):
        app.logger.info('[get_languages] Using existing sorted_lang.json...')
        try:
            with open(PATH_sorted_lang, 'r') as f:
                return jsonify(json.loads(f.read())), 200
        except:
            app.logger.error('[get_languages] Failed reading %s', PATH_sorted_lang, exc_info=True)

    return jsonify(generate_working_server()), 200


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
@app.route(URI_prefix + '/files/<file_uid>', methods = ['PUT'])
def put_file(file_uid):
    # Code for decode base64
    #f.write(base64.b64decode(data['file_contents']))

    # Check if the file exist or not
    if os.path.exists(PATH_PREFIX_file_cache + file_uid):
        # To save cpu cycle, we just ignore it if the requested file exists.
        return '', 204
    else:
        try:
            data = request.get_data()
            with open(PATH_PREFIX_file_cache + file_uid, 'wb') as f:
                f.write(data)
            return '', 204
        except:
            app.logger.error('[put_file] Something went wrong writing file "%s"', file_uid)
            return '', 500


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
@app.route(URI_prefix + '/files/<file_uid>', methods = ['HEAD'])
def check_file(file_uid):
    # Check if the file exist or not
    if os.path.exists(PATH_PREFIX_file_cache + file_uid):
        return '', 204
    else:
        return '', 404


#======================================================
# API call: submit_run
#
# The elephant in the room. It check if the file needed
# is in this proxy, then decide which jobe server to
# sned to and retrive and return result back to client.
#
# Returns:
#  200 when the runs is sucessful and with result
#  202 when the run is pending on jobe
#   - which is impossible because jobe server only runs
#   in immediate mode right now
#  400 on illegal parameter
#  404 when file needed is not found on the proxy
#======================================================
@app.route(URI_prefix + '/runs', methods = ['POST'])
def submit_runs():
    request_data = request.get_json()
    # TODO: Check parameters
    #if 'run_spec' in request_data

    # Check if the file(s) exist on the proxy
    file_list = request_data['run_spec']['file_list']
    for file_pair in file_list:
        if not os.path.exists(PATH_PREFIX_file_cache + file_pair[0]):
            return '', 404

    # THE MEAT of the whole project: Choose a Jobe server
    # Read in working_server.json
    working_server = None
    try:
        with open(PATH_working_server, 'r') as f:
            working_server = json.loads(f.read())
    except:
        app.logger.error('[submit_run] Failed reading %s', PATH_working_server, exc_info=True)
        return '', 500

    # Use random for now
    jobe_url = load_balance.lb_random(working_server, request_data['run_spec']['language_id'])
    if jobe_url == 'Nope':
        app.logger.error("[submit_run] Don't use __weight as language id!!")
        return '', 500

    app.logger.info('[submit_run] Selected Jobe server: %s', jobe_url)

    # Send files to Jobe is there's any
    for file_pair in file_list:
        try:
            r = None
            with open(PATH_PREFIX_file_cache + file_pair[0], 'r') as f:
                r = requests.put(jobe_url + '/jobe/index.php/restapi/files/' + file_pair[0], data = json.loads(f.read())) # cahnge to json instead of data?
            r.raise_for_status()
        except:
            app.logger.error('[submit_run] Somthing went wrong when uploading file(s) to: %s. Respond code: %i', jobe_url, r.status_code)
            return '', 500

    # Send run request to jobe and return the result
    try:
        r = None
        r = requests.post(jobe_url + '/jobe/index.php/restapi/runs', json = request_data, timeout = TTL_jobe_submit_runs)
        r.raise_for_status()
        return jsonify(r.json()), r.status_code
    except requests.Timeout:
        app.logger.error('[submit_run] Jobe server: %s timeout, maybe the server is dead?', jobe_url)
        return '', 408
    except requests.ConnectionError:
        app.logger.error('[submit_run] Error connecting to Jobe server: %s, maybe the server is dead?', jobe_url)
        return '', 500
    except:
        app.logger.error('[submit_run] Jobe server: %s respond with code: %i', jobe_url , r.status_code)
        return '', r.status_code


#======================================================
# API call: post_file
#
# Like the name sugguests, it put files in the server
# via POST request in parameter file_contents.
#
# It save the file to this proxy instead of the actual
# jobe server until submit_run is called.
#
# Since isn't implemented by jobe yet, it only return
# 403 in the current state.
#
# Returns:
# =========ONLY RESPONSES 403 IN CURRENT STATE=========
#  200 on success
#  400 on contents are not a valid base-64 encoding
#======================================================
@app.route(URI_prefix + '/files', methods = ['POST'])
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
# =========ONLY RESPONSES 404 IN CURRENT STATE=========
#======================================================
@app.route(URI_prefix + '/runresults/id', methods = ['GET'])
def get_run_status():
    return '', 404


#======================================================
# Not in the API call: force_update
#
# It force update working_server.json and
# sorted_lang.json.
# 
# It does the same thing when genrating these two but
# without the file pre-checks.
# 
# Returns:
# 
#======================================================
@app.route(URI_prefix + '/force_update', methods = ['GET'])
def force_update():
    return jsonify(generate_working_server()), 200


#======================================================
# Generate new working_server.json and 
# sorted_lang.json.
# Pulled form get_languages to be an method.
#======================================================
def generate_working_server():
    # First we read in jobe_list.json
    app.logger.info('[get_languages] Generating new working_server.json and sorted_lang.json...')
    jobe_list = ''
    try:
        with open(PATH_joeb_list, 'r') as f:
            jobe_list = json.loads(f.read())
    except:
        app.logger.error('[get_languages] Failed reading %s', PATH_joeb_list, exc_info=True)
        return []
    # Then we request each and every server one the list.
    # TODO: Refactor/rework this part? Need to add weight value into working_server.json
    working_server = dict()
    for server in jobe_list['jobe']:
        r = None
        lang_list = None
        for i in range(3): # try 3 times before moving on.
            try:
                r = requests.get(server['url'] + '/jobe/index.php/restapi/languages', timeout = TTL_jobe_get_languages)
                r.raise_for_status()
                lang_list = r.json()
                lang_list.append(['__weight', server['weight']])
                working_server[server['url']] = utils.list_of_list_to_dict(lang_list)
                break
            except requests.exceptions.HTTPError:
                app.logger.error('[get_languages] %s reposnse with %i', server['url'], r.status_code)
            except ValueError: # r.json()'s error
                app.logger.error('[get_languages] Error decoding json with server: %s', server['url'])
            except:
                app.logger.error('[get_languages] Error when requesting from : %s', server['url'])

    # Save to working_server.json.
    try:
        with open(PATH_working_server, 'w') as f:
            f.write(json.dumps(working_server))
    except:
        app.logger.error('[get_languages] Failed writing %s', PATH_working_server)
        return []

    # Compose reponse data from working_server to sorted_lang
    # TODO: Can these be simplified?
    sorted_lang_dict = dict()
    for server in working_server:
        for lang in working_server[server]:
            if lang not in sorted_lang_dict:
                sorted_lang_dict[lang] = [working_server[server][lang]]
            else:
                sorted_lang_dict[lang].append(working_server[server][lang])
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
        app.logger.error('get_languages] Failed writing %s', PATH_sorted_lang)
        return []

    return sorted_lang_list


if __name__ == '__main__':
    app.run()
