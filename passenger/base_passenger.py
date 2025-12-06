from abc import ABC, abstractmethod
from carrier.base_carrier import BaseCarrier

# TODO: Check if the role should be part of the BasePassenger class in some way
class BasePassenger(ABC):
    def __init__(self, carrier: BaseCarrier):
        self.carrier = carrier

        # Hand over of the received data from the carrier to the passenger via this callback
        self.carrier.set_callback(self.handle_incoming_data)

    @abstractmethod
    def handle_incoming_data(self, data):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
