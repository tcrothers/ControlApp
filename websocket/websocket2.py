from quart import render_template, websocket
from quart_trio import QuartTrio
import json
from app.resources import ConnectionManager
from app.mock_objs import mock_stages


class MovementException(Exception):
    def to_json(self):
        return json.dumps({"error": f'{self.args[0]}'})


app = QuartTrio(__name__)
stages = mock_stages

@app.route('/')
async def index():
    return await render_template('stage.html', stages=list(stages.values()))


app.xps_connections = ConnectionManager()


@app.websocket('/ws')
@app.xps_connections.collect_websocket  # decorator handles opening and closing
async def ws():
    # on page load function starts then heads into a loop
    try:
        while True:
            msg :str = await websocket.receive()
            if msg == "pong":
                print("heartbeat response")
                continue

            stage, command , new_stage_pos = msg.split(":")
            print(f"stage={stage}", f"cmd={command}", f"arg={new_stage_pos}")

            # display an error if stage is busy
            if stages[stage].is_busy():
                await websocket.send(json.dumps({"error" : f"{stage} busy"}))
                continue

            if command == "abs_move":
                app.nursery.start_soon(stages[stage].move_to, new_stage_pos)
            elif command == "rel_move":
                app.nursery.start_soon(stages[stage].move_by, new_stage_pos)

    finally:
        pass

    # called as client closes

        # async with trio.open_nursery() as nursery:
        # moving = trio.Event()
        # app.nursery.start_soon(stages[stage].move_to, new_stage_pos, moving)
        # app.nursery.start_soon(stages[stage].report, moving)
        # await websocket.send(f"{stages[stage].to_json()}")

if __name__ == '__main__':
    app.run(port=5000)
