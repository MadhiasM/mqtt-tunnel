import logging
import socket
import threading
from dataclasses import dataclass
from .base_passenger import BasePassenger
from carrier.base_carrier import BaseCarrier

logger = logging.getLogger(__name__)

@dataclass
class TcpPassengerConfig:
    role: str
    listen_port: int
    dst_port: int
    listen_ip: str = '0.0.0.0'
    dst_ip: str = '127.0.0.1'
    buffer_size: int = 65536

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
            logger.info(f"[TCP Client] Ready. Waiting for incoming data to connect to {self.cfg.dst_ip}:{self.cfg.dst_port}...")

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
        logger.info("[TCP] Passenger stopped.")

    def run(self):
        """
        Entry Point
        """
        self.running = True

        try:
            self.start()

            logger.info("[TCP] Program running. Press Ctrl+C to stop.")

            # Block the main thread until KeyboardInterrupt (not busy)
            threading.Event().wait()

        except KeyboardInterrupt:
            print()
            logger.info("[TCP] Stopping via Keyboard Interrupt...")
        finally:
            self.stop()

    def _run_server(self):
        """
        Create server and wait for inbound connections
        """
        self.server_socket = self._create_socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Auto-reconnect if old socket is not yet cleared by OS

        try:
            self.server_socket.bind((self.cfg.listen_ip, self.cfg.listen_port))
            self.server_socket.listen(1)
            logger.info(f"[TCP Server] Waiting for connections on {self.cfg.listen_ip}:{self.cfg.listen_port}...")

            while self.running:
                # Blocking wait for client
                client_sock, addr = self.server_socket.accept()
                logger.info(f"[TCP Server] Accepted connection from {addr}")

                # Common between server and client
                self._manage_active_connection(client_sock)

        except Exception as e:
            if self.running:
                logger.info(f"[TCP Server] Error: {e}")
        finally:
                # Close listener socket upon closing the thread
                if self.server_socket:
                    self.server_socket.close()

    def _connect_to_target(self):
        """
        Connects to the target host/port (Remote Role)
        """
        logger.info(f"[TCP Client] Connecting to {self.cfg.dst_ip}:{self.cfg.dst_port}...")
        try:
            sock = self._create_socket()
            sock.connect((self.cfg.dst_ip, self.cfg.dst_port))
            self.data_socket = sock
            threading.Thread(target=self._read_loop, daemon=True).start()
        except Exception as e:
            logger.info(f"[TCP Client] Connection failed: {e}")

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
                    break

                logger.debug(f"[{self.cfg.role}] TCP->MQTT {len(data)} bytes: {data[:64].hex()}")
                self.carrier.send(data)

        except Exception as e:
            logger.warning(f"[TCP] Connection lost: {e}")
        finally:
            logger.info("[TCP] Closing active connection")
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
                logger.debug(f"[{self.cfg.role}] MQTT->TCP {len(data)} bytes: {data[:64].hex()}")
                self.data_socket.send(data)
            except Exception as e:
                logger.error(f"[TCP] Write error: {e}")
                self.data_socket.close()
                self.data_socket = None
        else:
            logger.warning("[TCP] Warning: Data received but no active TCP connection.")
