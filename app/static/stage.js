var ws = new WebSocket('ws://' + document.domain + ':' + location.port + '/ws');

ws.onmessage = function (event) {
    var received_msg = JSON.parse(event.data);

    if (received_msg.hasOwnProperty("ping")){
        console.log("ping");
        this.send("pong");
        return
    }

    if (received_msg.hasOwnProperty("error")){
        let fade_error = function (error_content) {
            document.getElementById("MessageZone").textContent = "";
        };
        document.getElementById("MessageZone").textContent = received_msg["error"];
        setTimeout(fade_error, 5000);
        return
    }

    if (received_msg.hasOwnProperty("viewers")){
        console.log("updating viewers: " + received_msg.viewers);
        document.getElementById("viewer_count").textContent = "viewers : " + received_msg.viewers;
        return
    }


    let stage_name = received_msg.name;

    let row_to_update = document.getElementById(stage_name + "_row");
    let update_buttons = function (val) {
        for (let i = 0; i<buttons_per_row; i++) {
            let row_button = row_to_update.getElementsByTagName("button")[i];
            row_button.disabled = val;
        }
    };

    for (let field in received_msg) {
        if (field === "name") {
            continue
        }
        if (received_msg.hasOwnProperty(field)) {
            if (field === "state") {
                if (received_msg[field] === 44) {
                    update_buttons(true);
                } else if (received_msg[field] === 12) {
                    update_buttons(false);
                }
            }
            let cell_to_update = row_to_update.querySelector('[Headers=' + field + ']');
            cell_to_update.textContent = received_msg[field];
        }
    }
};

const buttons = [];
const callbacks = [":abs_move:", ":rel_move:-", ":rel_move:+"]
const buttons_per_row = callbacks.length;
const num_buttons = document.getElementsByTagName("button").length;

for (let i = 0; i<num_buttons; i++) {
    buttons[i] = document.getElementsByTagName('Button')[i];
    buttons[i].onclick = function () {
        let input_number = i - Math.floor( i / 3);

        if ((1+i) % buttons_per_row === 0) {
            input_number--;
        }
        let content = document.getElementsByTagName('input')[input_number].value;
        ws.send((this.name.split("_")[0]
            + callbacks[i % buttons_per_row]
            + content));
    };
}
