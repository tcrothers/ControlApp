var ws = new WebSocket('ws://' + document.domain + ':' + location.port + '/ws');

ws.onmessage = function (event) {
  var received_msg = event.data;
  var para1 = document.getElementsByTagName('p')[0];
  para1.textContent = received_msg;
};

var button = document.getElementsByTagName('Button')[0];
button.onclick = function() {
var content = document.getElementsByTagName('input')[0].value;
ws.send(content);
};
