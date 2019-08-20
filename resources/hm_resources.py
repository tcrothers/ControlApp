from resources.generic import SyncResource, ResManager
from pymodbus.client.sync import ModbusTcpClient

UNIT = 1
PORT = 502


class HmClient(ModbusTcpClient, SyncResource):

    def __init__(self, host, port=PORT):
        ModbusTcpClient.__init__(self, host=host, port=port)
        SyncResource.__init__(self, name=host)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return SyncResource.__exit__(self, exc_type, exc_val, exc_tb)

    def close(self):
        print("closing hm connection...")
        super().close()

    def cleanup(self, exc_type, exc_val, exc_tb):
        self.close()


class HmResManager(ResManager):
    def __init__(self, ip_addr):
        self.ip_addr = ip_addr
        super().__init__(max_resources=1)

    def _make(self):
        res = HmClient(self.ip_addr, port=PORT)
        print(f"new res: HM:{res.host}")
        return res
