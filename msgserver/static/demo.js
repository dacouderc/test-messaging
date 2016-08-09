
var socket;


/* Add log line to the #log div */
function addLog(className, message) {
    var elem = document.createElement('div');
    elem.className = className;
    elem.textContent = message;
    $('#log').append(elem);
}


/* Event handler for socketio errors */
function handleError(msg) {
    addLog('error', msg);
}


/* Event handler for receive_message handler: Another user sent us a message */
function handleMessage(msg) {
    addLog('message', msg['source'] + ':' + msg['body']);
}


/* Initialize socketio and connect event handle */
function setupConnection(username) {
    socket = io(undefined, {'query': "user=" + username});
    socket.on('error', handleError);
    socket.on('receive_message', handleMessage);
}


/* setup function */
$(function() {
    $('#connect-form :submit').click(function(ev) {
        ev.preventDefault();

        var username = $('#connect-form :text').val();
        if(username) {
            setupConnection(username);
            $('#connect-form').hide()
            $('#message-form').show()
        }
    });

    $('#message-form :submit').click(function(ev) {
        ev.preventDefault();

        var target = $('#target').val();
        var body = $('#body').val();

        if(target && body) {
            socket.emit('send_message', {
                'target': target,
                'body': body
            });

            addLog('info', 'Sending to ' + target + ': ' + body);
        }
    });
});
