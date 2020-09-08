import multiprocessing

bind = "10.147.17.251:8000"
workers = multiprocessing.cpu_count() * 2 + 1