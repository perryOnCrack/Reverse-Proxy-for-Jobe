#======================================================
# Some parameters
#======================================================
URI_prefix = '/jobe/index.php/restapi'

# File path to resourses
PATH_jobe_list = 'jobe_list.json'
PATH_PREFIX_file_cache = 'file_cache/'

# Some timeout params
TTL_working_server = 60 #180 # working_server.json's expire time (in sec.)
TTL_jobe_get_languages = 1 # request timeout on every jobe server when calling get_languages (in sec.)
TTL_jobe_submit_runs = 180 # request timeout on every jobe server when calling submit_runs (in sec.)