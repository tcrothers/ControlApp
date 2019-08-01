from app.intruments.instruments import Instrument, BaseInstrumentGroup
from typing import Iterable
import trio


class Step:
    def __init__(self, inst_in: Instrument, param_in, vals_in:Iterable):
        self.inst = inst_in
        self.parameter = param_in
        self.values = vals_in
        self.ready_state = trio.Event()

    async def listen_for_vals(self, recv_chan: trio.abc.ReceiveChannel):
        async with recv_chan:
            async for value in recv_chan:
                print(f"{self.inst.name} chan: got {value}")
                await self.set_next_val(value)
                self.ready_state.set()
        print("recv channel closed")

    async def set_next_val(self, val):
        await self.inst.set_param(self.parameter, val)

    async def report(self):
        # todo: probably get rid of this and measure more generally
        return await self.inst.get_param(self.parameter)


class Scan:
    # todo: make sure to clear steps after scan

    def __init__(self, all_insts: BaseInstrumentGroup):
        self.steps = []
        self._insts = all_insts
        self._send_channels = []
        self.running = False

    def add_step(self, inst_name: str, param, values):
        print("adding step...")
        inst_name = self._find_inst(inst_name)
        self.steps.append(Step(inst_name, param, values))

    async def run(self):
        self.running = True

        async with trio.open_nursery() as nursery:
            try:
                self._hand_out_channels(nursery)
                await self.run_step(pid=len(self.steps) - 1)
            finally:
                for chan in self._send_channels:
                    await chan.aclose()
                self._send_channels = []

        self.running = False
        # hand out mem channels for move-to commands
        # work recursively through steps firing off mem.send(val)
        # wait for all to be ready then measure

    def _hand_out_channels(self, nursery):

        for step in self.steps:
            send_chan, recv_chan = trio.open_memory_channel(0)
            self._send_channels.append(send_chan)
            nursery.start_soon(step.listen_for_vals, recv_chan)

    async def run_step(self, pid: int):

        current_chan = self._send_channels[pid]
        current_step = self.steps[pid]

        # todo could do this with events and move behaviour to step class?
        for val in current_step.values:
            current_step.ready_state.clear()
            await current_chan.send(val)
            if pid == 1:
                self._start_new_file()

            if pid == 0:
                await self._measure()
            else:
                await self.run_step(pid - 1)

    def _start_new_file(self):
        print("*** NEWFILE ***")

    async def _measure(self):
        print("measuring...")
        await self._wait_until_params_set()

        for step in self.steps:
            val = await step.report()
            print(f"{step.inst.name}: {val}")

    async def _wait_until_params_set(self):
        for step in self.steps:
            await step.ready_state.wait()

    def _find_inst(self, inst_name: str) -> Instrument:
        return self._insts.instruments[inst_name]

