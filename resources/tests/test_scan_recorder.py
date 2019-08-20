from resources.file_tools import ScanRecorder, StringBuilder
import os
import trio

fake_data = {"GROUP1:POS":40, "HM1.RegA":435, "HM1.RegB":445}
fake_data_2 = {"GROUP1:POS":45, "HM1.RegA":435, "HM1.RegB":446}


def test_sb(sep):
    sb = StringBuilder(sep=sep)
    sb.append('hello')
    sb.append('world')
    print(f"output:{sb.build()}")
    sb.append('hello')
    sb.append('world')
    print(f"output:{sb.build()}")


def test_make_unique_name():
    print("*" * 10, "testing make_unique_name", "*" * 10)
    rec = ScanRecorder()
    print(f"recorder folder: {rec.folder}, rec ext: {rec.ext}")
    print(os.listdir(rec.folder))
    name = rec._get_unique_name('test')
    print(f"suggested name = {name}")


def test_folder_exists():
    print("*" * 10, "testing folder exists", "*" * 10)
    rec = ScanRecorder()
    rec._check_folder()

async def sender(vals, send_chan: trio.abc.SendChannel):
    async with send_chan:
        for val in vals:
            print(f"sender sending: {val}")
            await send_chan.send(val)
            # await trio.sleep(1)
    print("closing sender")

async def sender_no_close(vals, send_chan: trio.abc.SendChannel):
    for val in vals:
        print(f"sender sending: {val}")
        await send_chan.send(val)
        # await trio.sleep(1)
    print("end no-closing sender")

async def test_writing():
    print("*" * 10, "testing write", "*" * 10)

    send_chan, recv_chan = trio.open_memory_channel(0)
    rec = ScanRecorder("test_write")
    async with trio.open_nursery() as nursery:
        nursery.start_soon(rec.receive_vals, recv_chan)
        nursery.start_soon(sender, [fake_data, fake_data, fake_data_2], send_chan)
    print("done")

async def test_multi_file_write():
    print("*" * 10, "testing two file write", "*" * 10)
    send_chan, recv_chan = trio.open_memory_channel(0)
    rec = ScanRecorder('test_multifiles')
    async with trio.open_nursery() as nursery:
        nursery.start_soon(rec.receive_vals, recv_chan)
        await sender_no_close([fake_data, fake_data, fake_data], send_chan)
        print("done file 1")
        await send_chan.send("NEWFILE")
        await sender_no_close([fake_data_2, fake_data_2, fake_data_2], send_chan)
        print("done file 2")
        await send_chan.aclose()

if __name__ == "__main__":
    # test_sb('')
    # test_sb('   ')
    # test_sb('\n')
    # test_folder_exists()
    # test_make_unique_name()
    trio.run(test_writing)
    trio.run(test_multi_file_write)