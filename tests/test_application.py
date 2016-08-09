"""
Unit tests for Application
"""
import mock
import pytest

from msgserver.application import Application

@pytest.fixture()
def app():
    app = Application()
    app.sio = mock.Mock()
    return app


def basic_auth(username):
    return 'Basic ' + (username + ':').encode('base64')


def test_connect(app):
    # connection without 'user' parameter are rejected
    assert app.connect('sid', {'QUERY_STRING': ''}) is False

    # accepted connection populates the user and connections list
    assert app.connect('sid1', {'QUERY_STRING': 'user=user1'}) is True

    assert 'user1' in app.users
    assert 'sid1' in app.connections

    # double connections are rejected
    assert app.connect('sid2', {'QUERY_STRING': 'user=user1'}) is False

    # resued socket id are rejected
    assert app.connect('sid1', {'QUERY_STRING': 'user=user2'}) is False


def test_disconnect(app):
    # connect 2 users
    app.connect('sid1', {'QUERY_STRING': 'user=user1'})
    app.connect('sid2', {'QUERY_STRING': 'user=user2'})
    assert set(app.connections.keys()) == {'sid1', 'sid2'}
    assert set(app.users.keys()) == {'user1', 'user2'}

    # then disconnect user1
    app.disconnect('sid1')

    # user and connection lists are updated
    assert set(app.connections.keys()) == {'sid2'}
    assert set(app.users.keys()) == {'user2'}


def test_send(app):
    app.connect('sid1', {'QUERY_STRING': 'user=user1'})

    # message must contain 'body' and 'target'
    app.send('sid1', {})
    app.sio.emit.assert_called_once_with('error', 'Invalid message', 'sid1')

    # message target must be connected
    app.sio.reset_mock()
    app.send('sid1', {'target': 'unknown', 'body': 'some message'})
    app.sio.emit.assert_called_once_with('error', 'Unknown recipient', 'sid1')

    # With a correct recipient, a message is emited to the recipient
    app.sio.reset_mock()
    app.connect('sid2', {'QUERY_STRING': 'user=user2'})
    app.send('sid1', {'target': 'user2', 'body': 'some message'})
    app.sio.emit.assert_called_once_with('receive_message', {
        'source': 'user1',
        'body': 'some message'
    }, 'sid2')
