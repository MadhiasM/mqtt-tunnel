import logging
import socket
import threading
from dataclasses import dataclass
from .base_passenger import BasePassenger
from carrier.base_carrier import BaseCarrier

logger = logging.getLogger(__name__)

@dataclass
class UdpPassengerConfig:
    role: str
    listen_port: int
    dst_port: int
    listen_ip: str = '0.0.0.0'
    dst_ip: str = '127.0.0.1'
    buffer_size: int = 65536

class UdpPassenger(BasePassenger):

  def __init__(self, carrier: BaseCarrier, config: UdpPassengerConfig):
    super().__init__(carrier)
    self.carrier = carrier
    self.cfg = config

    self.socket = None
    self.running = False
    self.addr = None

    try:
       self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
       if(self.cfg.role == 'local'):
         self.socket.bind( (self.cfg.listen_ip, self.cfg.listen_port) )
       logger.info(f"[UDP Server] Waiting for data on {self.cfg.listen_ip}:{self.cfg.listen_port}...")
    except Exception as e:
       logger.info(f"[UDP] Error: {e}")

  
  def handle_incoming_data(self, data):
     if self.cfg.role == 'local':
       # in case we get something before we have self.addr
       if self.addr:
        logger.debug(f"[{self.cfg.role}] MQTT->TCP {len(data)} bytes: {data[:64].hex()}")
        self.socket.sendto(data, self.addr)
     elif self.cfg.role == 'remote':
       self.socket.sendto(data, (self.cfg.dst_ip, self.cfg.dst_port) )

  # only used by Remote role
  def _run_listen(self):
    logger.info(f"[UDP Server] Waiting for connections on {self.cfg.listen_ip}:{self.cfg.listen_port}...")
    while self.running:
      data, addr = self.socket.recvfrom(self.cfg.buffer_size)
      if(self.addr == None):
        logger.info(f"[UDP Server] data received from {addr}")
      self.addr = addr
      self.carrier.send(data)

  def _handle_local_incoming(self):
    while self.running:
      data, addr = self.socket.recvfrom(self.cfg.buffer_size)
      logger.debug(f"[{self.cfg.role}] TCP->MQTT {len(data)} bytes: {data[:64].hex()}")
      self.carrier.send(data)

  def start(self):
     self.carrier.start()
     if self.cfg.role == 'local':
       threading.Thread(target=self._run_listen, daemon=True).start()
     elif self.cfg.role == 'remote':
       threading.Thread(target=self._handle_local_incoming, daemon=True).start()


  def run(self):
    self.running = True
    try:
      self.start()
      logger.info("[UDP] Program running. Press Ctrl+C to stop.")
      # Block the main thread until KeyboardInterrupt (not busy)
      threading.Event().wait()
    except KeyboardInterrupt:
      print()
      logger.info("[UDP] Stopping via Keyboard Interrupt...")
    finally:
      self.stop()

     
  def stop(self):
    if self.socket:
      self.socket.close()
    logger.info("[UDP] Passenger stopped.")