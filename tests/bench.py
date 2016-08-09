"""
Estimate resource usage of the server
"""
import resource

import mock

from test_integration import server, connect


def get_cpu(pid):
    with open('/proc/{0}/stat'.format(pid)) as fp:
        parts = fp.read().split()
        return sum(int(item) for item in parts[13:17])



def get_rss(pid):
    with open('/proc/{0}/status'.format(pid)) as fp:
        for line in fp:
            if line.startswith('VmRSS'):
                return int(line.split()[1])


def test_memory(server):
    """
    Estimate memory usage per connection
    """
    resource.setrlimit(resource.RLIMIT_NOFILE, (2500, 2500))

    start_rss = get_rss(server.pid)

    # connect 1000 user
    conn_number = 1000

    conns = [
        connect(params={'user': 'user' + str(i)})
        for i in range(conn_number)
    ]

    # let 1 message in flight for each user
    for i in range(conn_number):
        target = conn_number - i - 1
        conns[i].emit('send_message', {'target': 'user' + str(target),
                                       'body': 'some-message'})

    end_rss = get_rss(server.pid)

    print server.pid, float(end_rss - start_rss) / conn_number, 'kb/user'


def test_cpu(server):
    """
    Estimate CPU usage per message transfer
    """
    capture = mock.Mock()

    with connect(params={'user': 'user1'}) as user1:
        with  connect(params={'user': 'user2'}) as user2:
            user2.on('receive_message', capture)

            start_cpu = get_cpu(server.pid)

            message_count = 10000
            batch_size = 1000

            # send 10000 messages from user1 and read them back with user2
            for _ in range(message_count / batch_size):
                for _ in range(batch_size):
                    user1.emit('send_message',
                               {'target': 'user2', 'body': 'some-message'})

                while capture.call_count < 1000:
                    user2.wait(0.1)

                capture.reset_mock()

    end_cpu = get_cpu(server.pid)
    cpu_time = (end_cpu - start_cpu) / 100.0

    print server.pid, message_count / cpu_time, 'msgs/s'
