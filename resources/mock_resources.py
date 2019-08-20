from resources.generic import AsyncResource, ResManager


class MockResource(AsyncResource):
    async def __aenter__(self):
        await self.work("aenter")
        return self

    async def cleanup(self, exc_type, exc_val, exc_tb):
        print(f"cleanup: {exc_type.__name__}, {exc_val},")

        if exc_type is ValueError:
            print("caught exception")
            self.is_intact = False
            handled = 1
        else:
            handled = 0

        return handled #not None and issubclass(exctype, self._exceptions)

    async def aclose(self):
        await self.shutdown_resource()

    async def shutdown_resource(self):
        await self.work("closing...")
        self.is_intact = False

    async def work(self, val):
        print(f"{self.name}: {val}")

    def __del__(self):
        print("res del")


class MockResManager(ResManager):

    def __init__(self):
        self.name_counter = 97
        super().__init__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ret = await super().__aexit__(exc_type, exc_val, exc_tb)
        print(f"res back\n res available:{self.resources_available()}, total:{self.current_resources}")
        return ret

    async def get_resource(self):
        res = await super().get_resource()
        print(f"got: {res.name}")
        return res

    async def _register_request(self):
        print(f"request: res available:{self.resources_available()}, total:{self.current_resources}")
        await super()._register_request()
        return

    def _make(self):
        res = MockResource(chr(self.name_counter))
        print(f"new res: {res.name}")
        self.name_counter += 1
        return res