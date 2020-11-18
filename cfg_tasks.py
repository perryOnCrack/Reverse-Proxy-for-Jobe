from celery import Celery
import json, requests, redis, utils, time, global_vars
from celery.utils.log import get_task_logger

logger = get_task_logger('task')


#======================================================
# Redis client object initializtion
#======================================================
redis_cache = redis.StrictRedis(host = 'localhost', port = 6379, db = 1, password = None, decode_responses = True)


#======================================================
# Celery app initializtion
#======================================================
app = Celery('cfg', broker = 'redis://localhost:6379/0', backend = 'redis://localhost:6379/0')


#======================================================
# Task: update_working_server()
#
# This is basically generate_working_server() function
# from before, but returns differently because of the 
# new structure.
# 
# Return:
# - True: When the operation is successful.
# - False: When the operation is unsuccessful.
#======================================================
@app.task
def update_working_server():
    # Can't set updating flag
    if not redis_cache.set('updating', 'yes'):
        return False
    
    # First we request jobe_list from redis
    jobe_list = None
    if redis_cache.exists('jobe_list') or update_jobe_list():
        jobe_list = json.loads(redis_cache.get('jobe_list'))
    else: # No jobe_list to be found.
        redis_cache.set('updating', 'no')
        return False

    # Then we request each and every server one the list.
    # TODO: Refactor/rework this part? Need to add weight value into working_server.json
    working_server = dict()
    for server in jobe_list['jobe']:
        r = None
        lang_list = None
        for i in range(3): # try 3 times before moving on.
            try:
                r = requests.get(server['url'] + '/jobe/index.php/restapi/languages', timeout = global_vars.TTL_jobe_get_languages)
                r.raise_for_status()
                lang_list = r.json()
                lang_list.append(['__weight', server['weight']])
                working_server[server['url']] = utils.list_of_list_to_dict(lang_list)
                break
            except requests.exceptions.HTTPError:
                logger.error('[get_languages] %s reposnse with %i', server['url'], r.status_code)
            except ValueError: # r.json()'s error
                logger.error('[get_languages] Error decoding json with server: %s', server['url'])
            except:
                logger.error('[get_languages] Error when requesting from : %s', server['url'])

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

    # Save to sorted_lang in Redis.
    if not redis_cache.set('sorted_lang', json.dumps(sorted_lang_list), ex=global_vars.TTL_working_server):
        redis_cache.set('updating', 'no')
        return False

    # Save to working_server in Redis.
    if not redis_cache.set('working_server', json.dumps(working_server), ex=global_vars.TTL_working_server):
        redis_cache.set('updating', 'no')
        return False
    
    redis_cache.set('updating', 'no')
    return True


#======================================================
# Task: get_data(data_name)
#
# This task is intended to only get working_server 
# and sorted_lang from the Redis db and return to the 
# caller.
# 
# Check working_server.json and sorted_lang.json's 
# modification time to determent if it needs to 
# generate new ones or using existing ones.
# If the either one of the keys exsist, generate or 
# wait for new ones to be generated.
# 
# Return:
# - [True, request_data]: When the operation is 
#   successful.
# - [False]: When the operation is unsuccessful.
#======================================================
@app.task
def get_data(data_name):
    if data_name == 'working_server' or data_name == 'sorted_lang':
        if redis_cache.exists('working_server', 'sorted_lang') != 2: # at least one of them is missing
            # Polling if it's updating.
            if redis_cache.get('updating') == 'yes':
                logger.info('[get_language] Waiting for config update...')
                while redis_cache.get('updating') == 'yes':
                    time.sleep(1)
            # Generate new ones if is not
            else:
                if update_working_server():
                    return [True, redis_cache.get(data_name)]
                else:
                    return [False]
        else: # The two is present
            return [True, redis_cache.get(data_name)]
    return [False]


#======================================================
# Task: update_jobe_list()
#
# As the name suggests, it update jobe_list in the db.
# It read the file and put the content into the db.
# 
# Return:
# - True: When the operation is successful.
# - False: When the operation is unsuccessful.
#======================================================
@app.task
def update_jobe_list():
    try:
        with open(global_vars.PATH_jobe_list, 'r') as f:
            if not redis_cache.set('jobe_list', f.read()):
                logger.error('[update_jobe_list] Writing jobe_list to redis failed.')
                return False
    except:
        logger.error('[update_jobe_list] Other error writing jobe_list to redis.', exc_info=all)
        return False
    return True


#======================================================
# Task: sus_jobe(jobe_url)
#
# It checks wether the jobe sever(id by jobe_url) is
# dead or not and changing data in redis if needed.
#
# This task is called when the proxy's submit_run
# suspect one of the jobes(id by jobe_url) is dead.
# 
# Return:
# - Nothing
#======================================================
@app.task
def sus_jobe(jobe_url):
    # just call update_working_server() for now
    update_working_server() # TODO: Change to handle the specific one.
    '''
    # Test that jobe like in update_working_server()
    for i in range(3): # try 3 times before moving on.
            try:
                r = requests.get(jobe_url + '/jobe/index.php/restapi/languages', timeout = global_vars.TTL_jobe_get_languages)
                r.raise_for_status()
                result = r.json() 
                break
            except:
    '''


#======================================================
# Write configs into Redis
#======================================================
update_jobe_list()
