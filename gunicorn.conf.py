import multiprocessing

bind = '127.0.0.1:4000'
workers = multiprocessing.cpu_count() * 2 + 1
'''
log_level = 'debug'
access_logfile = '/var/www/reverse_proxy_2/log/access.log'
access_logformat = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
error_logfile = '/var/www/reverse_proxy_2/log/error.log'
'''