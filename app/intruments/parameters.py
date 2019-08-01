import trio
import json
from app.intruments.errors import MovementException
from numpy import inf


class Parameter:
    # sets and reads value, handles logic about moving

    def __init__(self, name: str, parent: str, min_val: float = 0, max_val: float = inf):
        self.name = name
        self.parent = parent
        self.min_val = min_val
        self.max_val = max_val
        self.state = -1
        self._val = 0

    async def set_to(self, new_value):
        await self._set(new_value)

    async def read(self):
        await trio.sleep(0)
        return self._val

    def full_name(self):
        return ".".join([self.parent, self.name])

    async def to_json(self, decimals=3):
        current_value = await self.read()
        base_info = {
            "name": self.name, 'parent': self.parent, "state": self.state, "position": f"{current_value:.{decimals}f}"}
        return json.dumps(base_info)

    async def _set(self, new_value):
        self.state = 44
        new_value = int(new_value)
        if new_value > self._val:
            while new_value > self._val:
                self._val += 0.5
                await trio.sleep(0.25)
        else:
            while new_value < self._val:
                self._val -= 0.5
                await trio.sleep(0.25)
        self.state = 12

    def check_value_between_limits(self, new_value: float):
        if new_value < self.min_val or new_value > self.max_val:
            raise MovementException(
                f"{new_value} outside range of {self.full_name()} ({self.min_val} -> {self.max_val})")
