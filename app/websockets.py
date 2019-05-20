from app import app, stages
from quart import websocket
import json


@app.websocket('/ws')
@app.xps_connections.collect_websocket  # decorator handles opening and closing
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

            # display an error if stage is busy
            if stages[stage].is_busy():
                await websocket.send(json.dumps({"error": f"{stage} busy"}))
                continue

            if command == "abs_move":
                app.nursery.start_soon(stages[stage].move_to, command_arg)
            elif command == "rel_move":
                app.nursery.start_soon(stages[stage].move_by, command_arg)

    finally:
        pass

    # called as client closes
