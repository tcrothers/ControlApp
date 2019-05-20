from functools import wraps
import trio
from app import app
from quart import websocket
import json


class ConnectionManager():
    """ this class handles all websocket
        connections and communications
    """
    xps_watchers = set()
    sock = None

    def anyone_listening(self):
       return bool(self.xps_watchers)

    def collect_websocket(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await self.add_conn()
            try:
                return await func(*args, **kwargs)
            finally:
                # to garauntee cleanup start another process, otherwise async calldepth = 1
                await self.remove_conn()
                app.nursery.start_soon(self._update_viewers)
        return wrapper

    async def add_conn(self):
        if not self.anyone_listening():
            print("starting a socket")
            app.nursery.start_soon(self._heartbeat_task)
            # todo: start a socket
        print("con-man: adding connection")
        self.xps_watchers.add(websocket._get_current_object())
        await self._update_viewers()

    async def remove_conn(self, started=trio.TASK_STATUS_IGNORED):
        print("con_man: removing connection")
        self.xps_watchers.remove(websocket._get_current_object())
        started.started()
        if not self.anyone_listening():
            print("closing the socket")

    async def broadcast(self, message, convert=False):
        if convert:
            message = json.dumps(message)
        # todo: tell page how many clients are active
        for web_sock in self.xps_watchers:
            await web_sock.send(message)

    async def _update_viewers(self):
        print({'viewers': len(self.xps_watchers)})
        await self.broadcast({'viewers': len(self.xps_watchers)}, convert=True)

    async def _heartbeat_task(self):
        print("heartbeat started")
        while self.xps_watchers:
            await trio.sleep(2)
            await self.broadcast('{"ping" : ""}')
        print("exiting heartbeat")


app.xps_connections = ConnectionManager()
