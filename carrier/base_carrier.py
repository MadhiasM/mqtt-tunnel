# carrier/base_carrier.py
from abc import ABC, abstractmethod

class BaseCarrier(ABC):
    @abstractmethod
    def start(self):
        """Start the carrier connection"""
        pass

    @abstractmethod
    def stop(self):
        """Stop the carrier"""
        pass

    @abstractmethod
    def send(self, payload: bytes):
        """Send data via the carrier"""
        pass

    @abstractmethod
    def set_callback(self, callback_function):
        """Set the function to call when data arrives"""
        pass
