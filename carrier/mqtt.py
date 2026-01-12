import logging
import sys
import paho.mqtt.client as mqtt
from dataclasses import dataclass
from typing import Optional, Callable
from .base_carrier import BaseCarrier

logger = logging.getLogger(__name__)

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
    topic: str
    transport: str
    ws_path: str
    tls_allow_insecure: bool
    username: Optional[str] = None
    password: Optional[str] = None
    ca_certs: Optional[str] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    max_message_size: int = 268435456

class MqttCarrier(BaseCarrier):
    def __init__(self, config: MqttConfig):
        """
        :param on_message_callback: Function, that is called upon receiving a message, which is different depending on the passenger protocoll
        :param topic_pub: Topic on which this client publishes
        :param topic_sub: Topic to which this client subscribes
        """
        self.cfg = config

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            transport=self.cfg.transport
        )

        if self.cfg.transport == "websockets":
            self.client.ws_set_options(path=self.cfg.ws_path)

        topic_upstream = f"{self.cfg.topic}/upstream"
        topic_downstream = f"{self.cfg.topic}/downstream"
        if self.cfg.role == 'local':
            self.topic_pub, self.topic_sub = topic_upstream, topic_downstream
        elif self.cfg.role == 'remote':
            self.topic_pub, self.topic_sub = topic_downstream, topic_upstream
        else:
            role_error_msg = f"Invalid role: {self.cfg.role!r}. Expected 'local' or 'remote'."
            logger.error(msg)
            raise ValueError(msg)

        self.callback: Optional[Callable] = None
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        if self.cfg.username is not None:
            self.client.username_pw_set(self.cfg.username, self.cfg.password)
        if self.cfg.tls_allow_insecure:
            logger.warning("[MQTT] Allowing TLS connections without verifying the server name matches the certificate label.")
            self.client.tls_insecure_set(True)
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
        logger.info(f"[MQTT] Connecting to {self.cfg.host}...")
        try:
            self.client.connect(self.cfg.host, self.cfg.port, self.cfg.keep_alive_time)
        except Exception as e:
          logger.error(f"[MQTT]Connection failed: {e}")
          sys.exit(1)
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
        if len(payload) > self.cfg.max_message_size:
            payload_list = []
            for i in range(0, len(payload), self.cfg.max_message_size):
                payload_list.append(payload[i: i+ self.cfg.max_message_size])
            for sub_payload in payload_list:
                self.client.publish(self.topic_pub, sub_payload, self.cfg.qos)
        else:
            self.client.publish(self.topic_pub, payload, self.cfg.qos)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """
        Internal callback to subscribe to the subscribe topic on connection
        """
        logger.info(f"[MQTT] Connected (Code {reason_code}). Subscribing to {self.topic_sub}")
        client.subscribe(self.topic_sub)

    def _on_message(self, client, userdata, msg):
        """
        Internal callback handler to forward the payload to the passenger
        """
        if self.callback:
            self.callback(msg.payload)
