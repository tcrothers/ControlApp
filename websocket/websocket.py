from quart import render_template, websocket
from quart_trio import QuartTrio
import trio
from functools import wraps


app = QuartTrio(__name__)

app.connected = set()


def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print("wrapping: adding connection")
        app.connected.add(websocket._get_current_object())
        try:
            return await func(*args, **kwargs)
        finally:
            print("wrapper: removing connection")
            app.connected.remove(websocket._get_current_object())
    return wrapper

async def broadcast(message: str):
    active = len(app.connected)
    for websock in app.connected:
        await websock.send(f"Broadcast: {message.upper()} : to {active}")


@app.route('/')
async def index():
    return await render_template('index.html')


@app.websocket('/ws')
@collect_websocket
async def ws():
    await broadcast("new connection")
    try:
        while True:
            data: str = await websocket.receive()
            await websocket.send(f"got {data}")
            await trio.sleep(1)
            await broadcast(f"{data.upper()}")
    finally:
        print("client closed connection")


if __name__ == '__main__':
    app.run(port=5000)
