import socket
import threading
from dataclasses import dataclass
from .base_passenger import BasePassenger
from carrier.base_carrier import BaseCarrier # TODO: Really needed?
from typing import Optional, Callable

# TODO: Check if I need threading / async here.
# TODO: Check if Carrier should be imported here or only in main to remove dependency / coupling
# TODO: Check if the dependency on the role is necessary here od if there is a more elegant way
# TODO: Check if the if else between local and remote role can behandled in a more elegant way
# TODO: Check if dependency injection of the carrier into the passenger is the best option here, or if there can be some middle layer like core/link.py, which handles this.
# TODO: Use Strategy Pattern for the roles instead of if/else
# TODO: Check if lazy reconnect on remote is causing issues (lazy: only connect on the first message)
# TODO: Use logging instead of print
# TODO: Maybe create self.running Flag

@dataclass
class TcpPassengerConfig:
    port: int
    role: str
    host: Optional[str] = 'localhost'

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
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create stream (TCP) based IPv4 socket
        return s

    def start(self):
        """
        Create thread to run server or client instance
        """

        self.carrier.start()

        # TODO: Check if this if / else can be factored out, since the method is similar
        if self.cfg.role == 'local':
            # Server startet in eigenem Thread, damit er accept() loopen kann
            threading.Thread(target=self._run_server, daemon=True).start()

        elif self.cfg.role == 'remote':
            # Client versucht direkt zu verbinden
            threading.Thread(target=self._run_client, daemon=True).start()

    def stop(self):
        """
        Close the socket
        """
        self.running = False

        # TODO: Should the carrier be stopped here or in main?
        self.carrier.stop()

        # Close the data socket
        if self.data_socket:
            self.data_socket.close()
        # Closes the listener on server side
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

            # WICHTIG: Haupt-Thread blockieren, um die Daemon-Threads am Leben zu halten.
            # Da wir keine spezifische Aktion haben, die blockiert (wie socket.accept()),
            # verwenden wir hier eine einfache Abfrage.
            # Die elegante Lösung, die keine CPU verschwendet, basiert auf dem
            # einfachen Warten auf den KeyboardInterrupt des Benutzers.

            print("[TCP] Program running. Press Ctrl+C to stop.")

            # Dies blockiert den Haupt-Thread auf unbestimmte Zeit,
            # bis eine Unterbrechung (KeyboardInterrupt) erkannt wird.
            # Es verbraucht extrem wenig CPU, da es keine aktive Schleife ist.
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
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # SO_REUSEADD: Auto reconnect after crash or during bind() if old socket is not yet cleared by OS, only required for Server. SOL_SOCKET: socket layer

        try:
            self.server_socket.bind(("0.0.0.0", self.cfg.port))
            self.server_socket.listen(1)
            print(f"[TCP Server] Waiting for connections on port {self.cfg.port}...")

            while self.running:
                # Hier warten wir auf den Client (blockierend)
                client_sock, addr = self.server_socket.accept()
                print(f"[TCP Server] Accepted connection from {addr}")

                # AB HIER: Gemeinsamer Code!
                self._manage_active_connection(client_sock)

                # Hinweis: Wenn wir nur EINEN Client gleichzeitig wollen,
                # bleiben wir in _manage_active_connection hängen, bis er trennt.
                # Wenn wir mehrere wollen, müssten wir hier einen Thread starten.

        except OSError as e:
            if self.running:
                print(f"[TCP Server] Error: {e}")

    def _run_client(self):
        """
        Create client, which tries to connect
        """
        print(f"[TCP Client] Connecting to {self.cfg.host}:{self.cfg.port}...")

        # Einfacher Retry-Mechanismus könnte hier hin
        try:
            sock = self._create_socket()
            sock.connect((self.cfg.host, self.cfg.port))

            # AB HIER: Gemeinsamer Code!
            self._manage_active_connection(sock)

        except Exception as e:
            print(f"[TCP Client] Connection failed: {e}")
            # TODO: Hier wäre ein Retry sinnvoll

    def _manage_active_connection(self, socket_obj):
        """
        Upon connecting, forward data back and forth between carrier and passenger, no matter if client or server
        """
        self.data_socket = socket_obj

        try:
            while self.running:
                data = self.data_socket.recv(4096)
                if not data:
                    break # Verbindung vom Peer geschlossen

                # Daten vom TCP -> Carrier senden
                self.carrier.send(data)

        except Exception as e:
            print(f"[TCP] Connection lost: {e}")
        finally:
            print("[TCP] Closing active connection")
            self.data_socket.close()
            self.data_socket = None

    def handle_incoming_data(self, data):
        """
        Callback: data received from Carrier, write to Socket.
        """
        if self.data_socket:
            try:
                # self.data_socket.sendall(data) # TODO: Check if send or sendall shall be used
                self.data_socket.send(data)
            except Exception as e:
                print(f"[TCP] Write error: {e}")
                # Eventuell hier socket schließen, damit der Lese-Loop abbricht
                self.data_socket.close()
        else:
            print("[TCP] Warning: Data received but no active TCP connection.")
