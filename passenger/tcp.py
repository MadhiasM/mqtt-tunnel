import socket
import threading
from dataclasses import dataclass
from .base_passenger import BasePassenger
from carrier.base_carrier import BaseCarrier

@dataclass
class TcpPassengerConfig:
    port: int
    role: str
    buffer_size: int = 65536
    host: str = 'localhost'

class TcpPassenger(BasePassenger):
    def __init__(self, carrier: BaseCarrier, config: TcpPassengerConfig):
        super().__init__(carrier)
        self.cfg = config

        self.server_socket = None
        self.data_socket = None

        self.running = False

    def _create_socket(self):
        """
        Helper to create a standard TCP socket.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return s

    def start(self):
        """
        Create thread to run server or client instance
        """
        self.carrier.start()

        # NOTE: Role-based branching kept intentionally for now.
        # See README.md for refactor ideas (Strategy pattern).
        if self.cfg.role == 'local':
            # Server starts in own thread, to loop until connection is incoming and accepted
            threading.Thread(target=self._run_server, daemon=True).start()

        elif self.cfg.role == 'remote':
            # Client does not connect immediately, but waits for data (Lazy Connection).
            print(f"[TCP Client] Ready. Waiting for incoming data to connect to {self.cfg.host}:{self.cfg.port}...")

    def stop(self):
        """
        Close the socket
        """
        self.running = False

        self.carrier.stop()

        # Close the data socket
        if self.data_socket:
            self.data_socket.close()
        # Close the listener on server side
        if self.server_socket:
            self.server_socket.close()
        print("[TCP] Passenger stopped.")

    def run(self):
        """
        Entry Point
        """
        self.running = True

        try:
            self.start()

            print("[TCP] Program running. Press Ctrl+C to stop.")

            # Block the main thread until KeyboardInterrupt (not busy)
            threading.Event().wait()

        except KeyboardInterrupt:
            print("\n[TCP] Stopping via Keyboard Interrupt...")
        finally:
            self.stop()

    def _run_server(self):
        """
        Create server and wait for inbound connections
        """
        self.server_socket = self._create_socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Auto-reconnect if old socket is not yet cleared by OS, only required for Server

        try:
            self.server_socket.bind(("0.0.0.0", self.cfg.port))
            self.server_socket.listen(1)
            print(f"[TCP Server] Waiting for connections on port {self.cfg.port}...")

            while self.running:
                # Hier warten wir auf den Client (blockierend)
                client_sock, addr = self.server_socket.accept()
                print(f"[TCP Server] Accepted connection from {addr}")

                # Common between server and client
                self._manage_active_connection(client_sock)

        except Exception as e:
            if self.running:
                print(f"[TCP Server] Error: {e}")
        finally:
                # Close listener socket upon closing the thread
                if self.server_socket:
                    self.server_socket.close()

    def _connect_to_target(self):
        """
        Connects to the target host/port (Remote Role)
        """
        print(f"[TCP Client] Connecting to {self.cfg.host}:{self.cfg.port}...")
        try:
            sock = self._create_socket()
            sock.connect((self.cfg.host, self.cfg.port))
            self.data_socket = sock
            # Start reading thread
            threading.Thread(target=self._read_loop, daemon=True).start()
        except Exception as e:
            print(f"[TCP Client] Connection failed: {e}")

    def _manage_active_connection(self, socket_obj):
        """
        Upon connecting, forward data back and forth between carrier and passenger on server side.
        """
        self.data_socket = socket_obj
        self._read_loop()

    def _read_loop(self):
        """
        Reads from TCP socket and sends to Carrier.
        """
        try:
            while self.running and self.data_socket:
                data = self.data_socket.recv(self.cfg.buffer_size)
                if not data:
                    break # Connection closed by peer.

                #print(f"[{self.cfg.role}] TCP->MQTT {len(data)} bytes: {data[:64].hex()}")
                # Send data that was received from TCP socket to carrier
                self.carrier.send(data)

        except Exception as e:
            print(f"[TCP] Connection lost: {e}")
        finally:
            print("[TCP] Closing active connection")
            if self.data_socket:
                self.data_socket.close()
            self.data_socket = None

    def handle_incoming_data(self, data):
        """
        Callback: data received from Carrier, write to Socket.
        """
        # Lazy connection for Remote role
        if self.cfg.role == 'remote' and self.data_socket is None:
             self._connect_to_target()

        if self.data_socket:
            try:
                #print(f"[{self.cfg.role}] MQTT->TCP {len(data)} bytes: {data[:64].hex()}")
                self.data_socket.send(data)
            except Exception as e:
                print(f"[TCP] Write error: {e}")
                self.data_socket.close()
                self.data_socket = None
        else:
            print("[TCP] Warning: Data received but no active TCP connection.")
