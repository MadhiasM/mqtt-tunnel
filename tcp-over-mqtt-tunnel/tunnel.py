import json
import socket
import threading
import argparse
import paho.mqtt.client as mqtt

# MQTT Configuration (defaults)
_TOPIC_UP = "tunnel/c2s"     # Local -> Remote
_TOPIC_DOWN = "tunnel/s2c"   # Remote -> Local
_BUFFER_SIZE = 65536 # 65536 works more stable for following use cases: sftp, SOCKS Proxy
_KEEPALIVE = 60

# CLI overrides with help (parsed on import; tolerant of extra args)
_CLI_LISTEN_PORT = None
_CLI_TARGET_PORT = None
try:
    _parser = argparse.ArgumentParser(
        description=(
            "TCP-over-MQTT Tunnel\n"
            "- Run local_tunnel.py on the client side (listens locally and publishes to MQTT).\n"
            "- Run remote_tunnel.py on the server side (subscribes and forwards to the target service).\n\n"
            "Use the flags below to override runtime parameters."
        ),
        epilog=(
            "Examples:\n"
            "  python local_tunnel.py --listen-port 2022 --buffer-size 8192\n"
            "  python remote_tunnel.py --target-port 2222 --keepalive 120\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
    )
    _parser.add_argument("--buffer-size", type=int, dest="buffer_size",
                         help="TCP read buffer size in bytes (default: 4096)")
    _parser.add_argument("--keepalive", type=int, dest="keepalive",
                         help="MQTT keepalive time in seconds (default: 60)")
    _parser.add_argument("--listen-port", type=int, dest="listen_port",
                         help="Local tunnel listen port (local_tunnel.py only; default: 2222)")
    _parser.add_argument("--target-port", type=int, dest="target_port",
                         help="Target service port (remote_tunnel.py only; default: 22)")

    _args, _ = _parser.parse_known_args()

    if _args.buffer_size is not None:
        _BUFFER_SIZE = _args.buffer_size
    if _args.keepalive is not None:
        _KEEPALIVE = _args.keepalive
    _CLI_LISTEN_PORT = _args.listen_port
    _CLI_TARGET_PORT = _args.target_port
except SystemExit:
    # argparse -h/--help triggers SystemExit after printing help; let it bubble up
    raise
except Exception:
    # Leave defaults if parsing fails for any other reason
    pass


# Helpers
def _load_conf(path="config.json"):
    with open(path) as f:
        return json.load(f)


def _get_mqtt_config(conf):
    mode = conf.get("connection_type", "wan")  # default to secure option
    if mode == "lan":
        port = 1883
        use_tls = False
        use_auth = False
    elif mode == "wan":
        port = 8883
        use_tls = True
        use_auth = True
    else:
        raise ValueError(f"Invalid connection_type: {mode}")

    return {
        "host": conf["broker_host"],
        "port": port,
        "use_tls": use_tls,
        "use_auth": use_auth,
        "username": conf.get("username"),
        "password": conf.get("password"),
        "ca_path": conf.get("ca_path"),
    }


def _build_mqtt_client(mqtt_cfg, on_connect, on_message):
    client = mqtt.Client()
    if mqtt_cfg.get("use_auth"):
        client.username_pw_set(mqtt_cfg.get("username"), mqtt_cfg.get("password"))
    if mqtt_cfg.get("use_tls"):
        client.tls_set(
            ca_certs=mqtt_cfg.get("ca_path"),
            certfile=None,
            keyfile=None
        )
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_cfg["host"], mqtt_cfg["port"], _KEEPALIVE)
    return client


# Base and concrete tunnels
class BaseTunnel:
    """Common MQTT wiring for tunnel endpoints."""

    subscribe_topic = None  # must be set by subclass
    label = "Tunnel"

    def __init__(self, label=None):
        if label:
            self.label = label
        self.conf = _load_conf()
        self.mqtt_cfg = _get_mqtt_config(self.conf)
        self.mqtt = _build_mqtt_client(
            self.mqtt_cfg,
            on_connect=self.on_connect,
            on_message=self.on_message,
        )

    def on_connect(self, client, userdata, flags, rc):
        print(f"{self.label}: Verbunden mit Broker (Code {rc})")
        if self.subscribe_topic:
            client.subscribe(self.subscribe_topic)

    def on_message(self, client, userdata, msg):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError


class LocalTunnel(BaseTunnel):
    """Listens on a local TCP port and forwards to MQTT (_TOPIC_UP)."""

    subscribe_topic = _TOPIC_DOWN
    label = "Lokal"

    def __init__(self, listen_port=2222):
        super().__init__(label="Lokal")
        # CLI flag takes precedence over constructor/default
        self.listen_port = _CLI_LISTEN_PORT or listen_port
        self.active_socket = None

    def on_message(self, client, userdata, msg):
        """Write MQTT payload to the active local TCP socket."""
        if self.active_socket:
            try:
                self.active_socket.send(msg.payload)
            except Exception as e:
                print(f"{self.label}: Fehler beim Schreiben in Socket: {e}")

    def run(self):
        # MQTT in background; our TCP loop blocks in foreground
        self.mqtt.loop_start()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", self.listen_port))
        server.listen(1)

        print(f"{self.label}: Tunnel bereit auf Port {self.listen_port}. Warte auf Verbindung...")

        try:
            while True:
                client_sock, addr = server.accept()
                print(f"{self.label}: Neue Verbindung von {addr}")
                self.active_socket = client_sock

                while True:
                    data = client_sock.recv(_BUFFER_SIZE)
                    if not data:
                        break
                    self.mqtt.publish(_TOPIC_UP, data)

                client_sock.close()
                print(f"{self.label}: Verbindung geschlossen.")
                self.active_socket = None
        except KeyboardInterrupt:
            pass
        finally:
            try:
                server.close()
            finally:
                self.mqtt.loop_stop()


class RemoteTunnel(BaseTunnel):
    """Subscribes to _TOPIC_UP and forwards to a target TCP service; responses go to _TOPIC_DOWN."""

    subscribe_topic = _TOPIC_UP
    label = "Remote"

    def __init__(self, target_host="localhost", target_port=22):
        super().__init__(label="Remote")
        self.target_host = target_host
        # CLI flag takes precedence over constructor/default
        self.target_port = _CLI_TARGET_PORT or target_port
        self.target_socket = None

    def _handle_target_responses(self, sock):
        try:
            while True:
                data = sock.recv(_BUFFER_SIZE)
                if not data:
                    break
                self.mqtt.publish(_TOPIC_DOWN, data)
        except Exception as e:
            print(f"{self.label}: Fehler beim Lesen vom Target: {e}")
        finally:
            try:
                sock.close()
            finally:
                print(f"{self.label}: Verbindung zum Target beendet.")

    def on_message(self, client, userdata, msg):
        """Ensure target connection and forward MQTT payload to it."""
        if self.target_socket is None:
            try:
                print(f"{self.label}: Baue Verbindung zum Ziel-Dienst auf...")
                self.target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.target_socket.connect((self.target_host, self.target_port))
                t = threading.Thread(
                    target=self._handle_target_responses,
                    args=(self.target_socket,),
                    daemon=True,
                )
                t.start()
            except Exception as e:
                print(f"{self.label}: Fehler beim Verbinden zum Ziel: {e}")
                self.target_socket = None
                return

        try:
            self.target_socket.send(msg.payload)
        except Exception as e:
            print(f"{self.label}: Fehler beim Senden an Ziel: {e}")
            self.target_socket = None

    def run(self):
        print(f"{self.label}: Tunnel-Exit bereit. Leite weiter an {self.target_host}:{self.target_port}")
        # Blocking loop in foreground; response thread handles target recv
        self.mqtt.loop_forever()
