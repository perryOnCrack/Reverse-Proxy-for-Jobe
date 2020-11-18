import os, sys, json, time, base64
from flask import Flask, jsonify, request
import requests
import utils, load_balance, global_vars
import logging
import redis
import cfg_tasks
from utils import send_file_to_jobe


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
@app.route(global_vars.URI_prefix + '/languages', methods = ['GET'])
def get_languages():
    # Get data from Celery
    result = cfg_tasks.get_data.delay('sorted_lang').get()
    if result[0]:
        return jsonify(json.loads(result[1])), 200
    else: 
        return jsonify([]), 200


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
@app.route(global_vars.URI_prefix + '/files/<file_uid>', methods = ['PUT'])
def put_file(file_uid):
    # Code for decode base64
    #f.write(base64.b64decode(data['file_contents']))

    # Check if the file exist or not
    if os.path.exists(global_vars.PATH_PREFIX_file_cache + file_uid):
        # To save cpu cycle, we just ignore it if the requested file exists.
        return '', 204
    else:
        try:
            data = request.get_data()
            with open(global_vars.PATH_PREFIX_file_cache + file_uid, 'wb') as f:
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
@app.route(global_vars.URI_prefix + '/files/<file_uid>', methods = ['HEAD'])
def check_file(file_uid):
    # Check if the file exist or not
    if os.path.exists(global_vars.PATH_PREFIX_file_cache + file_uid):
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
@app.route(global_vars.URI_prefix + '/runs', methods = ['POST'])
def submit_runs():
    request_data = request.get_json()
    # TODO: Check parameters
    #if 'run_spec' in request_data

    # Check if the file(s) exist on the proxy
    file_list = request_data['run_spec']['file_list']
    for file_pair in file_list:
        if not os.path.exists(global_vars.PATH_PREFIX_file_cache + file_pair[0]):
            return '', 404

    # Read in working_server from Celery
    working_server = cfg_tasks.get_data.delay('working_server').get()
    if working_server[0]:
        working_server = json.loads(working_server[1])
    else:
        app.logger.error('[submit_run] Error loading working_server')
        return jsonify([]), 500 # TODO: Compose the right respose so coderunner can display error msg. (It can be done, right?)

    while True: # Auto resend loop
        # Choose a jobe URL from working_sever
        jobe_url = load_balance.lb_random(working_server, request_data['run_spec']['language_id']) # Use random for now
        if jobe_url == 'Nope':
            app.logger.error("[submit_run] Don't use __weight as language id!!")
            return '', 500 # TODO: Compose the right respose so coderunner can display error msg. (It can be done, right?)
        app.logger.info('[submit_run] Selected Jobe server: %s', jobe_url)

        # Send submit run to the server.
        # TODO: Log
        return_data = None
        return_code = None
        dead = False
        # First run:
        run_result = utils.send_run_to_jobe(jobe_url, request_data)
        if run_result[0]: # First run success
            return_data = run_result[1]
            return_code = 200
        elif run_result[2] == 404: # First run file not found
            send_file_result = utils.send_file_to_jobe(jobe_url, file_list)
            if send_file_result[0]: # Send file(s) success
                app.logger.info('[submit_run] File(s) sent to %s successfully', jobe_url)
                # Second run:
                run_result = utils.send_run_to_jobe(jobe_url, request_data)
                if run_result[0]: # Second run success
                    return_data = run_result[1]
                    return_code = 200
                else: # Second run fail
                    app.logger.warning('[submit_runs] Jobe: %s fail running submit, reason: %i, %s', jobe_url, run_result[2], run_result[3])
                    dead = True
            else: # Send file(s) fail
                app.logger.warning('[submit_runs] Fail sending file to Jobe: %s, reason: %i, %s', jobe_url, send_file_result[1], send_file_result[2])
                dead = True
        else: # First run fail
            app.logger.warning('[submit_runs] Jobe: %s fail running submit, reason: %i, %s', jobe_url, run_result[2], run_result[3])
            dead = True

        if dead:
            cfg_tasks.sus_jobe.delay(jobe_url)
            working_server.pop(jobe_url) # Exclude the jobe from local var
            if working_server == {}: # No more working server to choose
                app.logger.error("[submit_run] Running out of working server!!")
                return_data = ''
                return_code = 500
                break
        else:
            break

    return jsonify(return_data), return_code # TODO: Compose the right respose so coderunner can display error msg.


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
@app.route(global_vars.URI_prefix + '/files', methods = ['POST'])
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
@app.route(global_vars.URI_prefix + '/runresults/id', methods = ['GET'])
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
@app.route(global_vars.URI_prefix + '/force_update', methods = ['GET'])
def force_update():
    if cfg_tasks.update_jobe_list.delay().get():
        update_result = cfg_tasks.update_working_server.delay().get()
        if update_result:
            data_result = cfg_tasks.get_data.delay('sorted_lang').get()
            if data_result[0]:
                return jsonify(json.loads(cfg_tasks.get_data.delay('sorted_lang').get()[1])), 200
    return jsonify([]), 200


if __name__ == '__main__':
    app.run()
