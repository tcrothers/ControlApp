from quart import render_template, websocket, abort, current_app
from quart_trio import QuartTrio
from secrets import compare_digest
import trio
import json
from functools import wraps


class MovementException(Exception):
    def to_json(self):
        return json.dumps({"error": f'{self.args[0]}'})


class Stage:
    def __init__(self, name):
        self.name = name
        self.state = 12
        self.position: float = 0.0
        self.lo_lim: int = 0
        self.hi_lim: int = 100
        self._lock = trio.Lock()

    def is_busy(self):
        return self._lock.locked()

    def to_json(self):
        acc = 3
        base_info = {"name": self.name, "state": self.state, "position": f"{self.position:.{acc}f}"}
        return json.dumps(base_info)

    async def move_to(self, new_pos:str):
        target = int(new_pos)
        try:
            await self.check_target_pos(target)
            if self._lock.locked():
                raise MovementException(f"{self.name}: Stage Busy")
            async with self._lock:
                async with trio.open_nursery() as nursery:
                    self.state = 44
                    nursery.start_soon(self.broadcast_position)
                    await self._move(target)
                    nursery.cancel_scope.cancel()

                self.state = 12
                await app.xps_connections.broadcast(self.to_json())
        except MovementException as err:
            await websocket.send(err.to_json())

    async def _move(self, target):
        if target > self.position:
            while target > self.position:
                self.position += 0.5
                await trio.sleep(0.25)
        else:
            while target < self.position:
                self.position -= 0.5
                await trio.sleep(0.25)

    async def check_target_pos(self, target:float):
        if self.lo_lim > target or target > self.hi_lim:
            raise MovementException(
                f"{self.name}: target position '{target}' out of range ({self.lo_lim} -> {self.hi_lim})")

    async def move_by(self, displacement:str):
        target_pos = self.position + int(displacement)
        await self.move_to(target_pos)

    async def broadcast_position(self):
        broadcast = app.xps_connections.broadcast
        while True:
            await broadcast(self.to_json())
            await trio.sleep(0.25)
        print("movement stopped")


app = QuartTrio(__name__)


stage1 = Stage("GROUP1")
stage2 = Stage("GROUP2")
stage3 = Stage("GROUP3")
stage4 = Stage("GROUP4")

stages = {"GROUP1":stage1, "GROUP2":stage2,
          "GROUP3":stage3, "GROUP4":stage4}


@app.route('/')
async def index():
    return await render_template('stage.html', stages=list(stages.values()))


class ConnectionManager():
    """ this class handles all websocket
        connections and communications
    """
    xps_watchers = set()
    sock = None

    def anyone_listening(self):
       return bool(self.xps_watchers)

    def collect_websocket(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await self.add_conn()
            try:
                return await func(*args, **kwargs)
            finally:
                # to garauntee cleanup start another process, otherwise async calldepth = 1
                await self.remove_conn()
                app.nursery.start_soon(self._update_viewers)
        return wrapper

    async def add_conn(self):
        if not self.anyone_listening():
            print("starting a socket")
            # todo: start a socket
        print("con-man: adding connection")
        self.xps_watchers.add(websocket._get_current_object())

    async def remove_conn(self, started=trio.TASK_STATUS_IGNORED):
        print("con_man: removing connection")
        self.xps_watchers.remove(websocket._get_current_object())
        started.started()
        if not self.anyone_listening():
            print("closing the socket")

    async def broadcast(self, message, convert=False):
        if convert:
            message = json.dumps(message)
        # todo: tell page how many clients are active
        for web_sock in self.xps_watchers:
            await web_sock.send(message)

    async def _update_viewers(self):
        print({'viewers': len(self.xps_watchers)})
        await self.broadcast({'viewers': len(self.xps_watchers)}, convert=True)


app.xps_connections = ConnectionManager()


@app.websocket('/ws')
@app.xps_connections.collect_websocket  # decorator handles opening and closing
async def ws():
    # on page load function starts then heads into a loop
    try:
        while True:
            msg :str = await websocket.receive()
            stage, command , new_stage_pos = msg.split(":")
            print(f"stage={stage}", f"cmd={command}", f"arg={new_stage_pos}")

            # error checking of input
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
