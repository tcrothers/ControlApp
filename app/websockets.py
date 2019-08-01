from app import app, xps1
from quart import websocket
import json


@app.websocket('/ws')
@xps1.con_man.collect_websocket  # decorator handles opening and closing
async def ws():
    # on page load function starts then heads into a loop
    try:
        while True:
            msg: str = await websocket.receive()
            if msg == "pong":
                print("heartbeat response")
                continue

            stage, command, command_arg = msg.split(":")

            print(f"stage={stage}", f"cmd={command}", f"arg={command_arg}")

            inst_to_move = xps1.instruments[stage]
            param_to_set = 'Position'

            # display an error if stage is busy
            if inst_to_move.is_busy():
                await websocket.send(json.dumps({"error": f"{stage} busy"}))
                continue


            if command == "abs_move":
                app.nursery.start_soon(inst_to_move.set_param, param_to_set, command_arg)
            elif command == "rel_move":
                app.nursery.start_soon(inst_to_move.relative_adjust_parameter, param_to_set, command_arg)

    finally:
        pass

    # called as client closes
