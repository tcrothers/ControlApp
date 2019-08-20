from __future__ import annotations

import trio
from contextvars import ContextVar
from contextlib import AbstractAsyncContextManager, AbstractContextManager
import time
from abc import ABC, abstractmethod

loaned_resource = ContextVar('Loaned')


class BaseResource:
    def __init__(self, name):
        self.name = name
        self.is_intact = True
        self.last_use = None


class AsyncResource(BaseResource, AbstractAsyncContextManager):

    def __init__(self, name):
        super().__init__(name=name)

    async def shutdown_resource(self):
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            normal_exit = await self.cleanup(exc_type, exc_val, exc_tb)
        else:
            normal_exit = True
        return normal_exit

    async def cleanup(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def aclose(self):
        pass


class SyncResource(BaseResource, AbstractContextManager):

    def __init__(self, name):
        super().__init__(name=name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            normal_exit = self.cleanup(exc_type, exc_val, exc_tb)
        else:
            normal_exit = True
        return normal_exit

    @abstractmethod
    def cleanup(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def close(self):
        pass

    async def aclose(self):
        self.close()
        await trio.sleep(0)


class ResManager(ABC):
    """
     hands out, limits number of and ensures closing of resources
     usage:
     man = ResManager
     with man as resource:
        resource.do_stuff()

     # done, loaned res returned to manager
     man.teardown()
    """
    def __init__(self, max_resources=2):

        self.max_resources = max_resources
        self.current_resources = 0
        [s, r] = trio.open_memory_channel(max_resources)
        self.send_chan: trio.abc.SendChannel = s
        self.recv_chan:trio.abc.ReceiveChannel = r
        self.resource_lock = trio.Lock()
        self._mon_stop = None

    async def __aenter__(self):
        loaned_res = await self.get_resource()
        loaned_resource.set(loaned_res)
        return loaned_res

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        res = loaned_resource.get()
        if issubclass(res.__class__, AsyncResource):
            exit_code = await res.__aexit__(exc_type, exc_val, exc_tb)
        else:
            exit_code = res.__exit__(exc_type, exc_val, exc_tb)
        await self.return_res(res)
        return exit_code


    async def get_resource(self):
        async with self.resource_lock:
            await self._register_request()
        res = await self.recv_chan.receive()
        return res

    async def _register_request(self):
        if not self.resources_available() and self.current_resources < self.max_resources:
            await self._make_new_resource()
        return

    def resources_available(self):
        return self.recv_chan.statistics().current_buffer_used

    async def _make_new_resource(self):
        res = self._make()
        self.current_resources += 1
        await self.send_chan.send(res)

    @abstractmethod
    def _make(self):
        """
        :return: a new resource
        """
        return BaseResource("Name")

    async def return_res(self, res):
        if res.is_intact and self.max_resources != -1:
            res.last_use = time.time()
            async with self.resource_lock:
                await self.send_chan.send(res)
        else:
            self.current_resources -= 1
            print("discarding res")
        return

    async def monitor(self, check_rate, max_time, stop_signal: trio.Event):
        self._mon_stop = stop_signal
        while not stop_signal.is_set():
            if self.resources_available():
                async with self.resource_lock:
                    if self.resources_available():
                        res = await self.recv_chan.receive()
                        last_used = time.time() - res.last_use
                        print(f"{res.name}:mon: res last used {last_used}")
                        if last_used > max_time:
                            print(f"closing res {res.name}")
                            self.current_resources -= 1
                            await res.aclose()
                        else:
                            await self.send_chan.send(res)
            else:
                print("no resources")
            await trio.sleep(check_rate)
        self._mon_stop = None
        print("closing monitor...")

    async def teardown(self):
        self.max_resources = -1  # stop accepting returned resources
        if self._mon_stop is not None:
            self._mon_stop.set()
        print("teardown: closing send channel")
        await self.send_chan.aclose()
        async for res in self.recv_chan:
            await res.aclose()
        print("teardown: closing recv channel")
        await self.recv_chan.aclose()
