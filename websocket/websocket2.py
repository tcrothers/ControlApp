from quart import render_template, websocket
from quart_trio import QuartTrio
import trio
import json


class Stage:
    def __init__(self, name):
        self.name = name
        self.state = 12
        self.position = 0

    def to_json(self):
        return json.dumps(self.__dict__)

    async def move_to(self, new_pos, moving:trio.Event):
        moving.set()
        target = int(new_pos)
        if target > self.position:
            while target > self.position:
                self.position += 1
                await trio.sleep(0.5)
        else:
            while target < self.position:
                self.position -= 1
                await trio.sleep(0.5)
        moving.clear()
        return

    async def report(self, websocket, moving:trio.Event):
        await moving.wait()
        while moving.is_set():
            await websocket.send(f"{self.to_json()}")
            await trio.sleep(0.25)

app = QuartTrio(__name__)
stage1 = Stage("GROUP1")
stage2 = Stage("GROUP2")
stages = {"GROUP1":stage1, "GROUP2":stage2}


@app.route('/')
async def index():
    return await render_template('stage.html', stages=[stage1, stage2])


@app.websocket('/ws')
async def ws():
    while True:
        msg = await websocket.receive()
        stage, new_stage_pos = msg.split(":")
        # async with trio.open_nursery() as nursery:
        moving = trio.Event()
        app.nursery.start_soon(stages[stage].move_to, new_stage_pos, moving)
        app.nursery.start_soon(stages[stage].report, websocket, moving)
        # await websocket.send(f"{stages[stage].to_json()}")


if __name__ == '__main__':
    app.run(port=5000)
