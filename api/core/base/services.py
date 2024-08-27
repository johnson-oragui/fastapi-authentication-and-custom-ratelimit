from abc import ABC, abstractmethod

class Services(ABC):
    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def fetch(self):
        pass

    @abstractmethod
    def fetch_all(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def delete(self):
        pass