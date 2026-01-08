import paho.mqtt.client as mqtt
from dataclasses import dataclass
from typing import Optional, Callable
from .base_carrier import BaseCarrier

@dataclass
class MqttConfig:
    """
    :param host: Hostname or IP of the broker
    :param port: Port to the broker. 1883 (no TLS) or 8883 (TLS)
    :param config: Dict mit Host, Port, Auth etc.
    """
    host: str
    port: int
    role: str
    qos: int
    keep_alive_time: int
    username: Optional[str] = None
    password: Optional[str] = None
    ca_certs: Optional[str] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None

class MqttCarrier(BaseCarrier):
    def __init__(self, config: MqttConfig):
        """
        :param on_message_callback: Function, that is called upon receiving a message, which is different depending on the passenger protocoll
        :param topic_pub: Topic on which this client publishes
        :param topic_sub: Topic to which this client subscribes
        """
        self.cfg = config  # Store the whole config object

        # Setup Client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        topic_client_to_server = "tunnel/c2s"
        topic_server_to_client = "tunnel/s2c"
        if self.cfg.role == 'local':
            self.topic_pub, self.topic_sub = topic_client_to_server, topic_server_to_client
        elif self.cfg.role == 'remote':
            self.topic_pub, self.topic_sub = topic_server_to_client, topic_client_to_server
        else:
            raise ValueError(f"Invalid role: {self.cfg.role!r}. Expected 'local' or 'remote'.")

        self.callback: Optional[Callable] = None
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        if self.cfg.username is not None:
            self.client.username_pw_set(self.cfg.username, self.cfg.password)
        if self.cfg.ca_certs:
            self.client.tls_set(
                ca_certs=self.cfg.ca_certs,
                certfile=self.cfg.certfile,
                keyfile=self.cfg.keyfile,
            )

    def set_callback(self, callback_function):
        """Required by BaseCarrier"""
        self.callback = callback_function

    def start(self):
        """
        Connect the MQTT client to the broker and keep running
        """
        print(f"[MQTT] Connecting to {self.cfg.host}...")
        self.client.connect(self.cfg.host, self.cfg.port, self.cfg.keep_alive_time)
        self.client.loop_start()

    def stop(self):
        """
        Stop the MQTT client loop and disconnect
        """
        self.client.loop_stop()
        self.client.disconnect()

    def send(self, payload):
        """
        Public method to send the passenger data to the broker
        """
        self.client.publish(self.topic_pub, payload, self.cfg.qos)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """
        Internal callback to subscribe to the subscribe topic on connection
        """
        print(f"[MQTT] Connected (Code {reason_code}). Subscribing to {self.topic_sub}")
        client.subscribe(self.topic_sub)

    def _on_message(self, client, userdata, msg):
        """
        Internal callback handler to forward the payload to the passenger
        """
        if self.callback:
            self.callback(msg.payload)
