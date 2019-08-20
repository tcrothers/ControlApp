from instruments.generic import Parameter, Instrument, InstrumentGroup
import json
from numpy import inf


class StageParam(Parameter):

    def __init__(self, name: str, parent: Instrument,
                 min_val: float = 0, max_val: float = inf):
        self.state = -1
        super().__init__(name, parent, min_val=min_val, max_val=max_val)

    async def to_json(self, decimals=3):
        current_value = await self.read()
        base_info = {
            "name": self.name, 'parent': self.parent,
            "state": self.state, "position": f"{current_value:.{decimals}f}"}
        return json.dumps(base_info)

    async def _set(self, new_value):
        self.state = 44
        await super(StageParam, self)._set(new_value)
        self.state = 12


class NewportStage(Instrument):

    def add_parameters(self, list_of_dicts):
        for p in list_of_dicts:
            self.parameters[p['name']] = StageParam(p['name'], self, p['min_val'], p['max_val'])


class XpsGroup(InstrumentGroup):
    # container of a group of instruments
    # holds connection info and inst dict

    # todo get this to connect to the XPS on initialisation

    def add_instrument(self, name: str):
        hard_coded_parameters = [{"name": "Position", "min_val": 0, "max_val": 100}, ]

        self.instruments[name] = NewportStage(name, self.con_man, hard_coded_parameters)
        print(f"{self.name} has insts {[p.name for p in self.instruments.values()]}")
        for v in self.instruments.values():
            print(f"{v.name} has params {[p.full_name() for p in v.parameters.values()]}")
