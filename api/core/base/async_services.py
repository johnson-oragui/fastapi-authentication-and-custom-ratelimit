from abc import ABC, abstractmethod

class Services(ABC):
    @abstractmethod
    async def create(self):
        pass

    @abstractmethod
    async def fetch(self):
        pass

    @abstractmethod
    async def fetch_all(self):
        pass

    @abstractmethod
    async def update(self):
        pass

    @abstractmethod
    async def delete(self):
        pass