import socket
import threading
from dataclasses import dataclass
from .base_passenger import BasePassenger
from carrier.base_carrier import BaseCarrier

# TODO: Check if I need threading / async here.
# TODO: Check if Carrier should be imported here or only in main to remove dependency / coupling
# TODO: Check if the dependency on the role is necessary here od if there is a more elegant way
# TODO: Check if the if else between local and remote role can behandled in a more elegant way
# TODO: Check if dependency injection of the carrier into the passenger is the best option here, or if there can be some middle layer like core/link.py, which handles this.
# TODO: Use Strategy Pattern for the roles instead of if/else
# TODO: Check if lazy reconnect on remote is causing issues (lazy: only connect on the first message)
@dataclass
class TcpPassengerConfig:
    port: int
    role: str

class TcpPassenger(BasePassenger):
    def __init__(self, carrier: BaseCarrier, config: TcpPassengerConfig):
        super().__init__(carrier)
        self.cfg = config
        self.active_socket = None


    def handle_incoming_data(self, data):
        """
        Callback for when a message from the carrier is received.
        """

        if self.cfg.role == 'local':
            # Local: Forward MQTT data to the connected TCP client
            if self.active_socket:
                try:
                    self.active_socket.send(data)
                except Exception as e:
                    print(f"[TCP] Error sending data to socket: {e}")

        elif self.cfg.role == 'remote':
            # Remote: Forward MQTT data to the target service (e.g. SSH)
            if self.active_socket is None:
                self._connect_to_target()

            if self.active_socket:
                try:
                    self.active_socket.send(data)
                except Exception as e:
                    print(f"[TCP] Error sending to target: {e}")
                    self.active_socket = None

    def _read_loop(self, sock):
        """
        Reads from the target socket and forwards to the carrier.
        Equivalent to _handle_target_responses in the old tunnel.py.
        """
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                self.carrier.send(data)
        except Exception as e:
            print(f"[TCP] Error in read loop: {e}")
        finally:
            sock.close()
            if self.active_socket == sock:
                self.active_socket = None

    def _connect_to_target(self):
        """Helper for Remote role: Connect to the target service (e.g. port 22)"""
        try:
            print(f"[TCP] Connecting to target localhost:{self.cfg.port}...")
            self.active_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.active_socket.connect(("localhost", self.cfg.port))

            # Start a thread to read from the target and send back to carrier
            t = threading.Thread(target=self._read_loop, args=(self.active_socket,), daemon=True)
            t.start()
        except Exception as e:
            print(f"[TCP] Failed to connect to target: {e}")
            self.active_socket = None


    def start(self):
        # TODO: Check if this logic should be here or in the mqtt class or in main.py
        self.carrier.start()

        # Bind the socket to listen to the TCP stream on the listen_port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("0.0.0.0", self.cfg.port))
        self.server.listen(1)
        print(f"[TCP] Waiting for connections on port {self.cfg.port}...")

    def stop(self):
        # TODO: Check if start and stop should be in here
        self.carrier.stop()
        self.server.close()

    def run(self):
        self.start()
        try:
            while True:
                client_sock, addr = self.server.accept()
                print(f"[TCP] Client {addr} verbunden")
                self.active_socket = client_sock

                # Read TCP data and hand over to carrier
                # TODO: Check if this dependency between carrier and passenger should be here
                while True:
                    data = client_sock.recv(4096)
                    if not data:
                        break

                    # Passenger uses the carrier to send data
                    # TODO: Check if this dependency between carrier and passenger should be here
                    self.carrier.send(data)

                client_sock.close()
                self.active_socket = None
        finally:
            # TODO: Check if start and stop should be in here
            self.stop()
