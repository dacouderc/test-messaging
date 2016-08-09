import logging
import os
import resource
import sys

import socketio
import eventlet.wsgi

from flask import Flask, redirect
from flask.json import jsonify
from werkzeug import urls


STATIC_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), 'static'))

logger = logging.getLogger(__name__)


class Application(object):
    def __init__(self):
        # maps user names to socketio's socket identifier
        self.users = {}

        # reverse mapping of self.user
        self.connections = {}

        # Flask application
        self.app = None

        # Socket.io server
        self.sio = None

    def wsgi(self):
        """
        Initialize a wsgi app for the application.
        """
        self.app = Flask(__name__, static_folder=STATIC_DIR)
        self.sio = socketio.Server()

        # connect methods to events
        self.app.route('/')(self.home)
        self.app.route('/users')(self.users_list)

        self.sio.on('connect')(self.connect)
        self.sio.on('send_message')(self.send)
        self.sio.on('disconnect')(self.disconnect)

        return socketio.Middleware(self.sio, self.app)

    def home(self):
        """
        Just redirect to the html test page
        """
        return redirect("/static/demo.html")

    def users_list(self):
        """
        Dumps the list of users in json
        """
        return jsonify(self.users.keys())

    def connect(self, sid, environ):
        """
        Called on new client connection.
        Client must identify itself using the query string parameter 'user'

        :param str sid: socketio's socket identifier
        :param dict environ: wsgi environment

        :returns: True if connection is accepted False otherwise
        """
        params = urls.url_decode(environ['QUERY_STRING'])
        if 'user' not in params:
            return False

        username = params['user']

        if username in self.users:
            return False
        if sid in self.connections:
            return False

        self.users[username] = sid
        self.connections[sid] = username

        logger.info('New connection from %s', username)

        return True

    def disconnect(self, sid):
        """
        Called on client disconnect. Cleanup the users and connection maps

        :param str sid: socketio's socket identifier
        """
        if sid in self.connections:
            user = self.connections[sid]
            del self.connections[sid]
            del self.users[user]

    def send(self, sid, message):
        """
        Called when a client ask to send a message.

        :param str sid: socketio's socket identifier
        :param dict message: message have the form: ::
           {
             "target": <user to deliver the message to>
             "body": <the message to deliver>
           }
        """
        if not isinstance(message, dict) or \
           'target' not in message or \
           'body' not in message:
            self.sio.emit('error', 'Invalid message', sid)
            return None

        if sid not in self.connections:
            self.sio.emit('error', 'Unknown socket ID', sid)
            return None

        if message['target'] not in self.users:
            self.sio.emit('error', 'Unknown recipient', sid)
            return None

        logger.info('Relaying message from %s to %s',
                    self.connections[sid],
                    message['target'])

        self.sio.emit('receive_message', {
            'source': self.connections[sid],
            'body': message['body']
        }, self.users[message['target']])



def main():
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: msgserver <IP>:<PORT>\n")
        sys.exit(1)

    (_, hard) = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))

    ip, port = sys.argv[1].split(':', 1)

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.WARNING)
    logger.setLevel(logging.INFO)

    app = Application()

    eventlet.wsgi.server(
        eventlet.listen((ip, int(port))),
        app.wsgi(),
        max_size=10000)



if __name__ == '__main__':
    main()
