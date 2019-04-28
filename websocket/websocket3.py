import trio
from quart_trio import QuartTrio
from contextlib import asynccontextmanager


app = QuartTrio(__name__)


@asynccontextmanager
async def open_websocket(url):
    async with trio.open_nursery() as nursery:
        async with WebSocket(nursery, url) as ws:
            await ws.connect()
            yield ws


class WebSocket(trio.abc.AsyncResource):
    def __init__(self, nursery, url):
        self._nursery = nursery
        self.url = url

    async def connect(self):
        # set up the connection

        ...
        # start the heartbeat task
        self._nursery.start_soon(self._heartbeat_task, kill_switch)
        return kill_switch

    async def _heartbeat_task(self, kill_switch:trio.Event):
        while not kill_switch.is_set():
            await trio.sleep(1)
            # stuff

    async def aclose(self):
        # close the nursery
        self._nursery.cancel_scope.cancel()

        # you'll need some way to shut down the heartbeat task here

    async def stop_task(self, kill_switch:trio.Event):
        kill_switch.set()


async with open_websocket as ws:
    await ws.send("hello")
