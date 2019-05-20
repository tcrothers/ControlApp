from quart_trio import QuartTrio
from quart import websocket
import trio

app = QuartTrio(__name__)


@app.websocket("/ws")
async def web_sock():
    print("connected")
    try:
        happy = True
        while happy:
            with trio.move_on_after(0.5) as test_reply:
                await websocket.send(f"ping")
                reply = await websocket.receive()
                assert reply == "pong"
            if test_reply.cancel_called:
                happy = False
                print("timed out")
            await trio.sleep(1)
    finally:
        print("exiting")
    #     await websocket.aclose()


async def main():
    test_client = app.test_client()
    print("made client")
    data = "bob"
    async with test_client.websocket('/ws') as test_websocket:
        with trio.move_on_after(5):
            while True:
                data = await test_websocket.receive()
                print(data)
                await trio.sleep(1)
                await test_websocket.send(f"pong")
    print("test done")


print("running main")
trio.run(main)
