import socket
import threading
from dataclasses import dataclass
from carrier.base_carrier import BaseCarrier

@dataclass
class UdpPassengerConfig:
    role: str
    listen_port: int
    send_port: int
    listen_ip: str = '0.0.0.0'
    send_ip: str = '127.0.0.1'
    buffer_size: int = 65536
    host: str = 'localhost'

class UdpPassenger():

  def __init__(self, carrier: BaseCarrier, config: UdpPassengerConfig):
    carrier.set_on_message_callback(self._on_message);
    self.carrier = carrier
    self.cfg = config

    self.socket = None
    self.running = False
    self.addr = None

    try:
       self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
       if(self.cfg.role == 'local'):
         self.socket.bind( (self.cfg.listen_ip, self.cfg.listen_port) )
       print(f"[UDP Server] Listening on {self.cfg.listen_ip}:{self.cfg.listen_port}")
    except Exception as e:
       print(f"[UDP Server] Error: {e}")

  
  def _on_message(self, msg):
     if self.cfg.role == 'local':
       # REMOVE AFTER
       print("on_message local")
       print(f"Forwarding to {self.addr}")
       self.socket.sendto(msg, self.addr)
     elif self.cfg.role == 'remote':
       # REMOVE AFTER
       print("on_message remote")
       print(f"Forwarding to {self.cfg.send_ip}:{self.cfg.send_port}")
       self.socket.sendto(msg, (self.cfg.send_ip, self.cfg.send_port) )

  # only used by Remote role
  def _run_listen(self):
    while self.running:
      data, addr = self.socket.recvfrom(self.cfg.buffer_size)
      # REMOVE AFTER
      if(self.addr == None):
        print(f"Addr received:")
        print(addr)
      self.addr = addr


      # print(f"Recevied on listen: {data} of type: {type(data)}")
      # forward traffic to mqtt
      self.carrier.send(data)

  def _handle_local_incoming(self):
    while self.running:
      data, addr = self.socket.recvfrom(self.cfg.buffer_size)
      # REMOVE AFTER
      print("GOT DATA FROM LOCAL SERVER BACK TO OTHER CLIENT")
      self.carrier.send(data)

  def start(self):
     self.carrier.start()
     if self.cfg.role == 'local':
       threading.Thread(target=self._run_listen, daemon=True).start()
     elif self.cfg.role == 'remote':
       threading.Thread(target=self._handle_local_incoming, daemon=True).start()
       print(f"[UDP Client] Ready. Waiting for incoming data to connect to {self.cfg.host}:{self.cfg.send_port}...")


  def run(self):
    self.running = True
    try:
      self.start()
      print("[UDP] Program running. Press Ctrl+C to stop.")
      # Block the main thread until KeyboardInterrupt (not busy)
      threading.Event().wait()
    except KeyboardInterrupt:
      print("\n[UDP] Stopping via Keyboard Interrupt...")
    finally:
      self.stop()

     
  def stop(self):
     if self.socket:
        self.socket.close()