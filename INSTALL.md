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

### Set Up Gunicorn



### Set Up Celery



### Set Up Redis



---