from abc import abstractmethod


class ConGroupBase:
    @abstractmethod
    async def broadcast_until_stopped(self, message):
        print(message)

    @abstractmethod
    async def broadcast(self, message):
        print(message)
