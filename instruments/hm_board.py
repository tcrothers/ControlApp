from __future__ import annotations
from abc import abstractmethod
from resources.hm_resources import HmResManager, UNIT
from instruments.generic import InstrumentGroup, Instrument, Parameter
from resources.base import ConGroupBase
from math import inf


# todo: need to add some sort of error handling for in case the board times out...

class Register(Parameter):
    read_length: int

    def __init__(self, name: str, parent: HmInstrument,
                 read_addr: int, write_addr: int, min_val=0, max_val=inf):
        super().__init__(name, parent, min_val=min_val, max_val=max_val)
        self.read_addr = read_addr
        self.write_addr = write_addr
        self.writable = write_addr is not None
        self.mod_man = parent.mod_man

    @abstractmethod
    async def read(self):
        pass


class InputRegister(Register):
    read_length = 16

    async def read(self):
        async with self.mod_man as client:
            val = client.read_input_registers(self.read_addr, self.read_length, unit=UNIT)
        self._val = val
        return val


class HoldingRegister(Register):
    read_length = 1

    async def read(self):
        async with self.mod_man as client:
            val = client.read_holding_registers(self.read_addr, self.read_length, unit=UNIT)
        self._val = val
        return val

    async def set_to(self, new_value):
        if self.write_addr is None:
            raise ValueError("cannot write to this reg")
        async with self.mod_man as client:
            val = client.write_registers(self.read_addr, 1, unit=UNIT)
        return val


class HmInstrument(Instrument):
    # have input registers as a parameter
    def __init__(self, name: str, con_man: ConGroupBase, mod_man: HmResManager):
        super().__init__(name, con_man)
        self.mod_man = mod_man

    def add_holding_register(self, name, read_addr, write_addr, min_val=0, max_val=inf):
        self.parameters[name] = HoldingRegister(
            name, self, read_addr, write_addr, min_val=min_val, max_val=max_val)

    def add_input_register(self, name, read_addr, write_addr, min_val=0, max_val=inf):
        self.parameters[name] = InputRegister(
            name, self, read_addr, write_addr, min_val=min_val, max_val=max_val)

    # todo: make this a param?
    def get_dt(self):
        with self.mod_man as client:
            client.read_input_registers(0, 16, 1)

    def get_t_thz(self):
        pass


class HmInstGroup(InstrumentGroup):
    def __init__(self, name, nursery, host, port):
        self.modbus_manager = HmResManager(ip_addr=host)
        super().__init__(name, nursery, host=host, port=port)
        # todo: start the monitor
        self.add_instrument()

    # todo: don't need this anymore I think? maybe an intialise for XPS instead?
    def connect_to_hardware(self):
        #print(f"{self.name} connecting to hardware...")
        #self.modbus_manager.connect()
        async with self.modbus_manager as client:
            #todo: add reg read -- check the version etc
            pass
        print(f"pretending modbus at {self.host}:{self.port} connected")

    def add_instrument(self):
        self.instruments[self.name] = HmInstrument(self.name, con_man=self.con_man, mod_man=self.modbus_manager)
        print(f"{self.name} has insts {[p.name for p in self.instruments.values()]}")

class Hm_builder:
    pass
