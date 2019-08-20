from _contextvars import ContextVar

from resources.generic import ResManager
from resources.mock_resources import MockResource, MockResManager
import trio
from random import random

######################## tests #######################
PID = ContextVar('PID')

async def test_get_resource(res_man, pid):
    PID.set(pid)

    res = await res_man.get_resource()
    async with res as r:
        await r.work(f"{PID.get()}: in loop")
        await trio.sleep(0.5)

    print(f"{PID.get()}: returning")
    await res_man.return_res(res)


async def test_borrow_and_break(res_man, pid):
    PID.set(pid)

    res = await res_man.get_resource()
    async with res as r:
        await r.work(f"{PID.get()}: in loop")
        await trio.sleep(0.5)
        if random() > 0.5:
            raise ValueError("res broken")

    print(f"{PID.get()}: returning")
    await res_man.return_res(res)


async def test_resManager():
    res_man = MockResManager()
    stop = trio.Event()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(res_man.monitor, 5, 20, stop)
        nursery.start_soon(test_get_resource, res_man, 1)
        nursery.start_soon(test_borrow_and_break, res_man, 2)
        nursery.start_soon(test_borrow_and_break, res_man, 3)
        await trio.sleep(2)
        await res_man.teardown()
    # print([res.name for res in res_man.resources])
    print("all done")


async def test_stats():
    # shows that need to call stats each time.
    send_chan, recv_chan = trio.open_memory_channel(2)
    stat = send_chan.statistics()
    async with send_chan:
        print(stat)
        await send_chan.send("hello")
        print(stat)
        stat = send_chan.statistics()
        print(stat)
    print("done")


async def test_man_borrow():
    res_man = MockResManager()
    stop = trio.Event()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(managed_borrow, res_man)
        nursery.start_soon(managed_borrow, res_man, True)
        nursery.start_soon(managed_borrow, res_man)
        await trio.sleep(2)
    await res_man.teardown()


async def managed_borrow(man: ResManager, break_res=False):
    async with man as res:
        await res.work("using res...")
        await trio.sleep(2)
        if break_res:
            raise ValueError("bad error")
        await res.work("done using res...")


async def test_borrow():
    res_man = MockResManager()
    async with res_man as res:
        await res.work("using res...")
        print("throwing error")
        raise ValueError("bad error")
    print("out of loop")
    async with res_man as res:
        await res.work("using res again...")
        print("done with")
    print("out of loop")


async def test():
    async with MockResource("no err") as con:
        await con.work("in context")
    print("out of context")

    async with MockResource("err") as con:
        await con.work("in context")
        raise ValueError("bad error")
    print("out of context")


if __name__ == "__main__":
    trio.run(test_man_borrow)
