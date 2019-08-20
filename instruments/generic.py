from __future__ import annotations
import trio
from resources.base import ConGroupBase
from instruments.errors import MovementException
from quart import websocket
import json

# InstGroup.Instrument.Parameter
# XPS.Stage.Position   = grouped
# HMBoard.CurtainDown  = ungrouped


class Parameter:
    # sets and reads value, handles logic about moving

    def __init__(self, name: str, parent: Instrument,
                 min_val: float, max_val: float):
        self.name = name
        self._parent = parent
        self.parent = parent.name
        self.min_val = min_val
        self.max_val = max_val
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
            "name": self.name, 'parent': self.parent, "position": f"{current_value:.{decimals}f}"}
        return json.dumps(base_info)

    async def _set(self, new_value):
        new_value = int(new_value)
        if new_value > self._val:
            while new_value > self._val:
                self._val += 0.5
                await trio.sleep(0.25)
        else:
            while new_value < self._val:
                self._val -= 0.5
                await trio.sleep(0.25)

    def check_value_between_limits(self, new_value: float):
        if new_value < self.min_val or new_value > self.max_val:
            raise MovementException(
                f"{new_value} outside range of {self.full_name()} ({self.min_val} -> {self.max_val})")


class Instrument:
    # container of parameters, marks them busy,
    # passes values to Parameters and broadcasts updates of params

    def __init__(self, name: str, con_man: ConGroupBase, params_in: list = None):
        self.keep_broadcasting_updates = con_man.broadcast_until_stopped
        self.broadcast = con_man.broadcast
        self.parameters = {}
        self.name = name
        self._lock = trio.Lock()
        if params_in:
            self.add_parameters(params_in)

    def add_parameters(self, list_of_dicts):
        for p in list_of_dicts:
            self.parameters[p['name']] = Parameter(p['name'], self, p['min_val'], p['max_val'])

    async def relative_adjust_parameter(self, param_name: str, displacement):
        try:
            if type(displacement) is str:
                displacement = self._convert_to_float(displacement)

            param: Parameter = self._get_param(param_name)
            new_value = await param.read() + displacement
            await self._set_param(param, new_value)
        except MovementException as err:
            await websocket.send(err.to_json())

    async def set_param(self, param_name: str, new_value):
        # try:
            if type(new_value) is str:
                new_value = self._convert_to_float(new_value)

            param: Parameter = self._get_param(param_name)
            await self._set_param(param, new_value)
        # except MovementException as err:
        #     await websocket.send(err.to_json())

    async def _set_param(self, param: Parameter, new_value: float):
        param.check_value_between_limits(new_value)

        if self.is_busy():
            raise MovementException(f"{self.name}: Stage Busy")
        async with self._lock:
            async with trio.open_nursery() as nursery:
                stop_signal = trio.Event()
                nursery.start_soon(self.keep_broadcasting_updates, param.to_json, stop_signal)
                await param.set_to(new_value)
                stop_signal.set()

            await self.broadcast(await param.to_json())

    async def get_param(self, param_name: str):
        param = self._get_param(param_name)
        return await param.read()

    def is_busy(self):
        return self._lock.locked()

    def to_json(self):
        base_info = {"name": self.name}
        return json.dumps(base_info)

    def _get_param(self, param_name):
        if param_name not in self.parameters:
            raise KeyError()
        return self.parameters[param_name]

    @staticmethod
    def _convert_to_float(input_str: str) -> float:
        try:
            input_as_float = float(input_str)
            return input_as_float
        except ValueError:
            raise MovementException(f'unable to convert "{input_str}" to float')


class BaseInstrumentGroup:
    # the base group used to keep track of all instruments,
    # while not having any network connection
    def __init__(self, name: str):
        self.name = name
        self.instruments = {}

    async def param_query_all(self, param: str, param_queries: list = None):
        output = {}
        for inst_name, inst_obj in self.instruments.items():
            output[inst_name] = {}

            if param == 'all':
                for param_name, param_obj in inst_obj.parameters.items():
                    output[inst_name][param_name] = await self._query_param(param_obj, param_queries)
            else:
                param_obj = inst_obj.parameters[param]
                output[inst_name][param] = await self._query_param(param_obj, param_queries)
        return output

    async def _query_param(self, param_obj: Parameter, param_queries: list = None):
        param_dict = {}
        for val in param_queries:
            if val == param_obj.name:
                param_dict[val] = await param_obj.read()
            else:
                param_dict[val] = getattr(param_obj, val)
        return param_dict


class InstrumentGroup(BaseInstrumentGroup):
    # container of a group of instruments
    # holds connection info and inst dict
    # socks: set  # actual sockets

    def __init__(self, name: str, con_man: ConGroupBase, host: str, port: int):
        super().__init__(name)
        self.host = host
        self.port = port
        self.con_man = con_man  # manages websockets
        self.connect_to_hardware()


    def connect_to_hardware(self):
        print(f"{self.name} pretending to connect to hardware...")
