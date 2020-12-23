# Reverse Proxy for [Jobe](https://github.com/trampgeek/jobe)

## What's this thing?

### It's a [reverse proxy ](https://en.wikipedia.org/wiki/Reverse_proxy) made to proxy multiple Jobe Sandboxes for load distrubution.

It follows Jobe's API so it can be deployed without changing Coderunner and Jobe's code.

Coderunner sees it as a normal Jobe and Jobe sees it as a normal client.

---

## Installation

There's quite a lot of compoments that needs to be connected in order to work.

### First thing first, clone this repo onto your machine

```
git clone https://github.com/perryOnCrack/Reverse-Proxy-for-Jobe.git
```

### Virtual Enviroment

Before installing any packages, I suggest using a virtual enviorment for this application. If you don't want to, feel free to skip this step.

The commands below use [python's own virtual enviorment](https://docs.python.org/3/library/venv.html)

* Create a new virtual enviorment

```
python3 -m venv /path/to/new/virtual/environment
```

* Activate the virtual enviorment

```
source /path/to/new/virtual/environment/bin/activate
```

After activating the virtual enviorment, you should be able to see your virtual enviorment name appears on your shell prompt.

---

If you have any questions feel free to submit an [issue](https://github.com/perryOnCrack/Reverse-Proxy-for-Jobe/issues),