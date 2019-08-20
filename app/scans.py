from __future__ import annotations
from instruments.generic import Instrument, BaseInstrumentGroup
from resources.file_tools import ScanRecorder
import trio


class Measurement(object):
    """
        This class represents a parameter to be measured
        """

    def __init__(self, inst_in: Instrument, param_in: str):
        self.inst: Instrument = inst_in
        self.parameter = param_in
        self.id = f"{inst_in.name}:{param_in}"

    async def measure(self):
        return await self.inst.get_param(self.parameter)


class Step(Measurement):
    def __init__(self, inst_in: Instrument, param_in: str, vals_in, step_number: int):
        super().__init__(inst_in, param_in)
        self.values = vals_in
        self.step_number = step_number
        self.busy = False
        self.send_ready_signal, self.recv_ready_signal = trio.open_memory_channel(0)

    async def listen_for_vals(self, recv_chan: trio.abc.ReceiveChannel):
        async with recv_chan:
            async for value in recv_chan:
                print(f"{self.inst.name} chan: got {value}")
                await self.set_next_val(value)
                self.busy = False
                await self.send_ready_signal.send(1)
        print("recv channel closed")

    async def set_next_val(self, val):
        await self.inst.set_param(self.parameter, val)

    def render_values(self):
        if len(self.values) > 10:
            rendered = str(self.values[0:3]).strip('[]') + " ... " + str(self.values[-1])
        else:
            rendered = str(self.values)
        return rendered


class Scan:
    # todo: make sure to clear steps after scan

    def __init__(self, all_insts: BaseInstrumentGroup):
        self.steps = []
        self.measurements = []
        self._insts = all_insts
        self._send_channels = []
        self.stop_signal = trio.Event()
        self.running = False
        self.write_file = None

    def add_step(self, inst_name: str, param_name: str, values):
        print("adding step...")
        inst = self._find_inst(inst_name)
        n_steps = len(self.steps)
        self.steps.append(Step(inst, param_name, values, n_steps))

    def add_measurement(self, inst_name: str, param_name: str):
        print("adding measurement...")
        inst = self._find_inst(inst_name)
        self.measurements.append(Measurement(inst, param_name))

    def remove_step(self, target_step: int):
        target = self.steps.pop(target_step)
        self.measurements.pop()
        for step in self.steps:
            step.step_number -= 1
        return target

    async def run(self, scan_name):
        self.running = True
        file_writer = ScanRecorder(scan_name)

        async with trio.open_nursery() as nursery:
            try:
                self._hand_out_channels(nursery)
                self._start_scan_recorder(nursery, file_writer)
                await self.run_step(pid=len(self.steps) - 1)
            finally:
                await self._cleanup_memory_channels()

        self.running = False
        self.stop_signal = trio.Event()

        # hand out mem channels for move-to commands
        # work recursively through steps firing off mem.send(val)
        # wait for all to be ready then measure

    async def _cleanup_memory_channels(self):
        for chan in self._send_channels:
            await chan.aclose()
        self._send_channels = []

        if self.write_file:
            await self.write_file.aclose()

        for step in self.steps:
            await step.send_ready_signal.aclose()
            step.send_ready_signal, step.recv_ready_signal = trio.open_memory_channel(0)

    def _hand_out_channels(self, nursery):

        for step in self.steps:
            send_chan, recv_chan = trio.open_memory_channel(0)
            self._send_channels.append(send_chan)
            nursery.start_soon(step.listen_for_vals, recv_chan)

    def _start_scan_recorder(self, nursery, file_writer: ScanRecorder):
        send_chan, recv_chan = trio.open_memory_channel(0)
        nursery.start_soon(file_writer.receive_vals, recv_chan)
        self.write_file = send_chan
        self._start_new_file = file_writer.new_file

    async def run_step(self, pid: int):

        current_chan = self._send_channels[pid]
        current_step = self.steps[pid]

        # todo could do this with events and move behaviour to step class?
        for val in current_step.values:
            # tell the instrument to move to next value
            current_step.busy = True
            await current_chan.send(val)
            if pid == 1:
                self._start_new_file()

            if pid == 0:
                results = await self._measure()
                await self.write_file.send(results)
            else:
                await self.run_step(pid - 1)

            if self.stop_signal.is_set():
                print("aborting measurement")
                break

    async def _measure(self):
        print("measuring...")
        await self._wait_until_params_set()

        vals = await self._measure_list(self.steps)
        vals.update(await self._measure_list(self.measurements))
        return vals

    async def _wait_until_params_set(self):
        for step in self.steps:
            if step.busy:
                ready = await step.recv_ready_signal.receive()
                # print(f"{step.inst.name} : ready = {ready}")
            else:
                pass
                # print(f"{step.inst.name} : was not busy")

    def _find_inst(self, inst_name: str) -> Instrument:
        return self._insts.instruments[inst_name]

    @staticmethod
    async def _measure_list(list_in) -> dict:
        values = {}
        for inst in list_in:
            values[inst.id] = await inst.measure()
        return values

