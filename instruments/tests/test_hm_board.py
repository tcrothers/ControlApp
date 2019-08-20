from instruments.hm_board import HmInstGroup
from resources.base import ConGroupBase

from codecs import decode
import trio


def read(ind, val):
    if ind == 3:
        val = parse_string(val)
    return val


def parse_string(v):
    return decode(format(v, 'x'), 'hex').decode('utf-8')


async def test_mod_man():
    async with trio.open_nursery() as nursery:
        hm1 = HmInstGroup("hm1", ConGroupBase(), '10.255.8.11', 502)

        reg_data = {}
        start_register = 0
        num_registers = 11
        result = await hm1.modbus_manager.read_holding_registers(start_register, num_registers)
        for i, v in enumerate(result.registers):
            reg_data[i + start_register] = v

        for k, v in reg_data.items():
            print(f"reg {k}: {read(k, v)}")


if __name__ == "__main__":
    trio.run(test_mod_man)