# Reverse Proxy for [Jobe](https://github.com/trampgeek/jobe)

## What's this thing?

### It's a [reverse proxy ](https://en.wikipedia.org/wiki/Reverse_proxy) made to proxy multiple Jobe Sandboxes for load distrubution and backend failure hiding(?).

It uses Gunicorn + Flask for its REST API, Celery for configurations' background tasks and Redis as a shared memory space for all the forked processes and Celery's message queue and backend.

## This README seems to be a bit empty...

Yeah, I know. I'll put more info when I got more time... 

Or leave me some questions in [issues](https://github.com/perryOnCrack/Reverse-Proxy-for-Jobe/issues) so I know what info you want to know about this project.