from quart import render_template, websocket
from quart_trio import QuartTrio
import trio


app = QuartTrio(__name__)


@app.route('/')
async def index():
    return await render_template('index.html')


@app.websocket('/ws')
async def ws():
    while True:
        data = await websocket.receive()
        await websocket.send(f"Received: {data}")
        await trio.sleep(1)
        for i in range(int(data)+1):
            await websocket.send(f"{i}")
            await trio.sleep(1)


if __name__ == '__main__':
    app.run(port=5000)
