import multiprocessing

#bind = '127.0.0.1:4000'
bind = '0.0.0.0:4000'
workers = 25
#threads = 4
timeout = 300 # 5 mins
#preload_app = True

# Logging configs
accesslog = '/var/log/gunicorn/jobe_rp.access.log'
errorlog = '/var/log/gunicorn/jobe_rp.error.log'
loglevel = 'info'

#access_logformat = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'