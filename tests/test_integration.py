import errno
import os
from subprocess import Popen
import resource
import socket
import sys
import time

import mock
import pytest
import requests
from socketIO_client import SocketIO
from socketIO_client.exceptions import ConnectionError


# port test server will listen to
TEST_SERVER_PORT = 35412
TEST_SERVER_URL = 'http://localhost:{}/'.format(TEST_SERVER_PORT)



# patch _close method of socketio client which does not close its HTTP connection on time
socketio_orig_close = SocketIO._close
def socketio_close(conn):
    socketio_orig_close(conn)
    if hasattr(conn, '_transport_instance'):
        conn._transport_instance._connection.close()
SocketIO._close = socketio_close


def port_is_open(addr):
    """
    Check if a socket can be opened on the given address
    """
    try:
        socket.create_connection(addr)
    except socket.error as e:
        if e.errno == errno.ECONNREFUSED:
            return False
        else:
            raise
    else:
        return True



def connect(**kw):
    return SocketIO('localhost', TEST_SERVER_PORT, wait_for_connection=False, **kw)


@pytest.yield_fixture()
def server():
    """
    Launch the test server process.

    This will be launched automically for the duration of each test
    """
    app_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '../msgserver/application.py')

    process = Popen([sys.executable,
                     app_file,
                     'localhost:' + str(TEST_SERVER_PORT)])
    try:
        while not port_is_open(('localhost', TEST_SERVER_PORT)) and process.poll() is None:
            time.sleep(0.1)

        process.poll()

        yield process
    finally:
        process.terminate()
        process.wait()


def test_connect(server):
    """
    Test connection to the server
    """
    param1 = {'user': 'user1'}

    # Connection without username are rejecter
    with pytest.raises(ConnectionError):
        connect()

    # Successull connection => user appears in user lists
    conn = connect(params=param1)
    try:
        assert 'user1' in requests.get(TEST_SERVER_URL + '/users').json()

        # Duplicate connections are rejected
        with pytest.raises(ConnectionError):
            connect(params=param1)
    finally:
        conn.disconnect()


def test_send(server):
    """
    Check delivery of messages
    """
    capture = mock.Mock()

    with connect(params={'user': 'user1'}) as user1:
        with  connect(params={'user': 'user2'}) as user2:
            user2.on('receive_message', capture)

            # send a message from user1 to user2
            user1.emit('send_message', {'target': 'user2', 'body': 'some-message'})
            user2.wait(0.1)

            # user2 received the message
            capture.assert_called_once_with({'source': 'user1', 'body': 'some-message'})


def test_send_error(server):
    """
    Check an error message is received when sending to an invalid target
    """
    capture = mock.Mock()
    param1 = {'user': 'user1'}

    with connect(params=param1) as user1:
        user1.on('error', capture)

        # send message to user2 which does not exists
        user1.emit('send_message', {'target': 'user2', 'body': 'some-message'})
        user1.wait(0.1)

        # error notification has been received
        capture.assert_called_once_with('Unknown recipient')
