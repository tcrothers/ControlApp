import trio
from app import app
from quart import websocket
import json


class MovementException(Exception):
    def to_json(self):
        return json.dumps({"error": f'{self.args[0]}'})


class Stage:
    def __init__(self, name):
        self.name = name
        # todo get rid of this state? redirect to calls to xps
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
                    # todo: remove hardcored state
                    self.state = 44
                    stop_broadcast = trio.Event()
                    nursery.start_soon(self.broadcast_position, stop_broadcast)
                    await self._move(target)
                    stop_broadcast.set()

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

    async def broadcast_position(self, stop_event:trio.Event):
        broadcast = app.xps_connections.broadcast
        while not stop_event.is_set():
            await broadcast(self.to_json())
            await trio.sleep(0.25)
        print("movement stopped")


stage1 = Stage("GROUP1")
stage2 = Stage("GROUP2")
stage3 = Stage("GROUP3")
stage4 = Stage("GROUP4")

stages = {"GROUP1":stage1, "GROUP2":stage2,
          "GROUP3":stage3, "GROUP4":stage4}