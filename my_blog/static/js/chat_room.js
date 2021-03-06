let ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";

const roomName = JSON.parse(document.getElementById('room-name').textContent);

const chatSocket = new WebSocket(
	ws_scheme + '://'
	+ window.location.host
	+ '/ws/chat/'
	+ roomName
	+ '/'
);
let chatSocketh = new WebSocket(
	ws_scheme + '://'
	+ window.location.host
	+ '/ws/push/'
	+ roomName
);

$('#connections').click(function () {
	$.ajax({
		url: "{% url 'push' %}",
		type: "get",
		data: {
			"room": roomName,
			"user": "{{ user_name }}",
			"user_conn": true,
			"csrfmiddlewaretoken": "{{ csrf_token }}"
		},
		success: function (data) {
			document.getElementById('total').innerHTML = ' ' + data.total_connection +' connection in total. Active users: ' + data.users;
		}
	})
})

chatSocket.onopen = function(e) {
	document.querySelector('#chat-log').value += ('Welcome to chat group ' + roomName + '!\n');
};

// onmessage - An event listener to be called when a message is received from the server.
chatSocket.onmessage = function(e) {
	// JSON.parse() converts the JSON object back into the original object,
	// then examine and act upon its contents.
	const data = JSON.parse(e.data);
	document.querySelector('#chat-log').value += (data.message + '\n');
};

chatSocketh.onmessage = function(e) {
	// JSON.parse() converts the JSON object back into the original object,
	// then examine and act upon its contents.
	let data = JSON.parse(e.data);
	if (data.message) {
		document.querySelector('#chat-log').value += (data.message + '\n');
	}};

// onclose - An event listener to be called when the connection is closed.
chatSocket.onclose = function(e) {
	console.error('Chat socket closed unexpectedly');
};

chatSocketh.onclose = function(e) {
	console.error('Chat socket closed unexpectedly');
};
document.querySelector('#chat-message-input').focus();
document.querySelector('#chat-message-input').onkeyup = function(e) {
	if (e.keyCode === 13) {  // enter, return
		document.querySelector('#chat-message-submit').click();
	}
};

document.querySelector('#chat-message-submit').onclick = function(e) {
	const messageInputDom = document.querySelector('#chat-message-input');
	const message = messageInputDom.value;
	
	// Send the msg object as a JSON-formatted string.
	chatSocket.send(JSON.stringify({
		'message': message
	}));
	
	// Blank the text input element, ready to receive the next line of text from the user.
	messageInputDom.value = '';
};