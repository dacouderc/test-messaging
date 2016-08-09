# Setup

Create a virtualenv and install the package into it

```
$ virtualenv env
$ . env/bin/activate
$ pip install -U setuptools
$ pip install .
```


# Usage

Server may be launched with the command:

```
$ msgserver localhost:8000
```

When connecting to the URL http://localhost:8000, a html demo page is diplayed.
It allows connecting to the server and sending messages to other users.
Sources for the demo are in msgserver/static.


To launch tests, use the command:
```
py.test tests
```
