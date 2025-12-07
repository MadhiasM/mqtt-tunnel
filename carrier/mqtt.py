import paho.mqtt.client as mqtt
from dataclasses import dataclass
from typing import Optional, Callable
from .base_carrier import BaseCarrier

# TODO: consider reconnect_on_failure in paho client
# TODO: consider transport: Literal['tcp', 'websockets', 'unix'] in paho client
#       TODO: Especially websockets, since it uses port 443 or 80, which are more often available
# TODO: Session control: tunnel/<session_id>/tx   # Endpoint A → Endpoint B
#       tunnel/<session_id>/c2s  - c2s / s2c or tx / rx
#       tunnel/<session_id>/ctrl - session control? Not sure if necessary
#       This would enable multiple (local) clients connecto to the remote client (VPN Server).
#       The remote host must be able to distinguish between multiple clients
#       But how to the two MQTT clients exchange their session_id?
#       If the remote client (VPN server) runs on the same server where the broker runs, maybe this will make it easier? He can handle this centralized and give out session_ids to ever client
# TODO: own Header within payload necessary?
# TODO: Consider https://pypi.org/project/asyncio-mqtt/
# TODO: Consider using Strategy Pattern for the roles instead of if/else
# TODO: Decide how the topics are exchange. Maybe one static exchange channel, through which the actual channels are negotioated? Or they have a shared config input? Or stay with static
# TODO: Local and Remote via Strategy Object, which is then passed into the MQTT Instance?
#       class LocalRole:
#           topic_pub = "tunnel/c2s"
#           topic_sub = "tunnel/s2c"
#       class RemoteRole:
#           topic_pub = "tunnel/s2c"
#           topic_sub = "tunnel/c2s"
# TODO: Use logging instead of print

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
    qos: int = 0 # TODO: since default is defined already in argparse, it does not need to be defined here again
    username: Optional[str] = None
    password: Optional[str] = None
    ca_certs: Optional[str] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    keep_alive_time: int = 60
    #topic_pub: str = ""
    #topic_sub: str = ""

class MqttCarrier(BaseCarrier):
    def __init__(self, config: MqttConfig):
        """
        :param on_message_callback: Function, that is called upon receiving a message, which is different depending on the passenger protocoll
        :param topic_pub: Topic on which this client publishes
        :param topic_sub: Topic to which this client subscribes
        """
        self.cfg = config  # Store the whole config object

        # Setup Client
        # TODO: Maybe replace with factory method build_mqtt_client(config)
        self.client = mqtt.Client()

        # TODO: Check if this should be configurable to allow multiple connections to be handled in parallel
        # TODO: Check if this logic should be in here or in main. Should the carrier know if it is on the local or remote machine? Or should it just blindly subscribe to the topic it is told to?
        # TODO: Include a session id like tunnel/<session_id>/rx
        topic_client_to_server = "tunnel/c2s"
        topic_server_to_client = "tunnel/s2c"
        if self.cfg.role == 'local':
            self.topic_pub, self.topic_sub = topic_client_to_server, topic_server_to_client
        elif self.cfg.role == 'remote':
            self.topic_pub, self.topic_sub = topic_server_to_client, topic_client_to_server
        # TODO: Decide if this check is necessary
        else:
            raise ValueError(f"Invalid role: {self.cfg.role!r}. Expected 'local' or 'remote'.")

        self.callback: Optional[Callable] = None
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        # Broker
        # TODO: Check if port should be validated between 1 and 65536
        #self.broker_host = self.cfg.host
        # TODO: Check if port should be validated between 1 and 65536
        #self.broker_port = self.cfg.port

        if self.cfg.username is not None:
            self.client.username_pw_set(self.cfg.username, self.cfg.password)
        if self.cfg.ca_certs:
            self.client.tls_set(
                ca_certs=self.cfg.ca_certs,
                certfile=self.cfg.certfile,
                keyfile=self.cfg.keyfile,
            )

    # TODO: Do I really need a setter function for that?
    def set_callback(self, callback_function):
        """Required by BaseCarrier"""
        self.callback = callback_function

    def start(self):
        """Connect the MQTT client to the broker and keep running"""
        print(f"[MQTT] Connecting to {self.cfg.host}...")
        self.client.connect(self.cfg.host, self.cfg.port, self.cfg.keep_alive_time)
        self.client.loop_start() # TODO: Decide wether to use loop_forever (blocking) or implement reconnection such as logic self.client.reconnect_delay_set(min_delay=1, max_delay=30)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def send(self, payload):
        """Public method for the passenger to send its payload to the broker"""
        self.client.publish(self.topic_pub, payload, self.cfg.qos)

    def _on_connect(self, client, userdata, flags, rc):
        """Internal callback to subscribe to the subscribe topic on connection"""
        print(f"[MQTT] Connected (Code {rc}). Subscribing to {self.topic_sub}")
        client.subscribe(self.topic_sub)

    def _on_message(self, client, userdata, msg):
        """Internal callback handler to forward the payload to the passenger"""
        if self.callback:
            self.callback(msg.payload)
