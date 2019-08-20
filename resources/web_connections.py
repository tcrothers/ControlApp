from resources.base import ConGroupBase
from app import app
from functools import wraps
import trio
from quart import websocket
import json


class ConnectionManager(ConGroupBase):
    """ this class handles all websocket connections and    f = await request.form
        communications for a group of instruments
    """
    def __init__(self):
        self.active_clients = set()
        self.sock = None

    def anyone_listening(self):
        return bool(self.active_clients)

    def collect_websocket(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await self.add_conn()
            try:
                return await func(*args, **kwargs)
            finally:
                # to garauntee cleanup start another process, otherwise async calldepth = 1
                await self.remove_conn()
                app.nursery.start_soon(self._update_clients)
        return wrapper

    async def add_conn(self):
        if not self.anyone_listening():
            print("starting a socket")
            app.nursery.start_soon(self._heartbeat_task)
            # todo: start a socket
        print("con-man: adding connection")
        self.active_clients.add(websocket._get_current_object())
        await self._update_clients()

    async def remove_conn(self, started=trio.TASK_STATUS_IGNORED):
        print("con_man: removing connection")
        self.active_clients.remove(websocket._get_current_object())
        started.started()
        if not self.anyone_listening():
            print("closing the socket")

    async def broadcast_until_stopped(self, generate_message: callable(None),
                                      stop_signal: trio.Event, update_interval=0.25):
        print("movement starting")
        while not stop_signal.is_set():
            msg = await generate_message()
            await self.broadcast(msg)
            await trio.sleep(update_interval)
        print("movement stopped")

    async def broadcast(self, message, convert=False):
        if convert:
            message = json.dumps(message)
        # todo: tell page how many clients are active
        for web_sock in self.active_clients:
            await web_sock.send(message)

    async def _update_clients(self):
        print({'viewers': len(self.active_clients)})
        await self.broadcast({'viewers': len(self.active_clients)}, convert=True)

    async def _heartbeat_task(self):
        print("heartbeat started")
        while self.active_clients:
            await trio.sleep(2)
            await self.broadcast('{"ping" : ""}')
        print("exiting heartbeat")
