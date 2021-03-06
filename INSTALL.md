# Installation

## Prerequisites

### OS

I develop this in a CentOS 8 virtual machine, but any Linux distro that can run python 3.8 should work just fine.

Windows users might need to look into other wsgi solutions.

### Softwares

Be sure to have **Python 3.8 (or above)** and **Docker** (for setting up Redis) installed.

---

## Installation

There's quite a lot of compoments that needs to be connected in order to work.

### First thing first, clone this repo onto your machine

```
git clone https://github.com/perryOnCrack/Reverse-Proxy-for-Jobe.git
```

### Set Up Virtual Enviroment

Before installing any packages, I suggest using a virtual enviorment for this application. If you don't want to use it, feel free to skip this step.

The commands below use [python's own virtual enviorment](https://docs.python.org/3/library/venv.html)

* Create a new virtual enviorment

```
python3 -m venv [virtual environment path]
```

* Activate the virtual enviorment

```
source [virtual environment path]/bin/activate
```

After activating the virtual enviorment, you should be able to see your virtual enviorment name appears on your shell prompt.

### Install packages

Run this command while in its folder.

```
pip install -r requirements.txt
```

If you're using virtual enviorment, be sure to check this folder to see if it actually install the packages into it.

```
[virtual environment path]/lib/python3.X/site-packages/
```

### Set Up User

Set up the account that will be used by Gunicorn and Celery.

```
sudo groupadd -r jobe_rp
sudo useradd -r -g jobe_rp -s /sbin/nologin jobe_rp
```

Add directory for log files.

```
sudo mkdir /var/log/jobe_rp
sudo chown jobe_rp:jobe_rp /var/log/jobe_rp
sudo chmod 0770 /var/log/jobe_rp
```

Be sure to add directory `file_cache` for file caching inside where you clone this repo to.

### Set Up Redis

It's quite simple, just run this docker command.

```
sudo docker run -d -p 127.0.0.1:6379:6379 --name redis-backend redis
```

It should install a redis instance on your machine running on localhost.

### Set Up Gunicorn as a systemd service

Copy `config/gunicorn.service` to `/etc/systemd/system` and edit the file.

Edit `WorkingDirectory`'s value to the location where you clone this repo.

Edit `ExecStart`

```
ExecStart=[Gunicorn binary path] -c [location where you clone this repo]/gunicorn.conf.py reverse_proxy:app
```

Start service

```
sudo systemctl startr gunicorn
```

### Set Up Celery as a systemd service

Copy `config/celery.service` to `/etc/systemd/system` and edit the file.

Edit `WorkingDirectory`'s value to the location where you clone this repo.

Edit `EnvironmentFile`

```
EnvironmentFile=[location where you clone this repo]/configs/celery
```

Edit `configs/celery.conf`

```
CELERY_BIN=[Celery binary path]
```

Start service

```
sudo systemctl startr celery
```


---