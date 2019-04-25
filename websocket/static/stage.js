var ws = new WebSocket('ws://' + document.domain + ':' + location.port + '/ws');

ws.onmessage = function (event) {
  let received_msg = JSON.parse(event.data);
  let stage_name = received_msg.name;

  let row_to_update = document.getElementById(stage_name + "_row");

  for (let field in received_msg) {
    if (field === "name") {
        continue
    }
    if (received_msg.hasOwnProperty(field)) {
      let cell_to_update = row_to_update.querySelector('[Headers=' + field + ']');
      cell_to_update.textContent = received_msg[field];
    }
  }
};

const num_buttons = document.getElementsByTagName("button").length;
const buttons = [];
for (let i = 0; i<num_buttons; i++) {
  buttons[i] = document.getElementsByTagName('Button')[i];
  let button_id = buttons[i].name.split("_button")[0];
  buttons[i].onclick = function() {
    let content = document.getElementsByTagName('input')[i].value;
    ws.send((button_id + ":" + content));
  }
}
