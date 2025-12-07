# TODO: tunnel.py or main.py
# TODO: argparse
# TODO: make the carrier and passenger configurable via CLI arguments
# TODO: Consider replacing print with logging.
# TODO: Enable Config.json additionally to CLI arguments
# TODO: If possible, make CLI arguments less dependent on the protocols used.
# TODO: Carrier and passenger should be able to be passed over via CLI argument (--carrier mqtt --passenger tcp)
# TODO: Bootstrap to start the remote client without having to manually start the carrier connection on that machine first, bu rather launch it from the local client
# TODO: decouple passenger and carrier, maybe some session object that enables communication between passenger and carrier without them knowing details about each other
# TODO: Consider handling of MTU, retransmission, sequencing, fragmentation/re-assembly through means of message headers/IDs handling within some separate module (framing?), maybe add some core/ directory for that
# TODO: Check if the handling of how the role is handed over to the passenger and carrier can be improved
# TODO: Include config.json, if not already done
# TODO: Bootstrap mechanism, that will automatically launch the remote side, if client connects to broker. If remote is running on broker, then maybe it can be handled there
#       TODO: Maybe some callback (on_connect - run the remote tunnel). Using this, there is no need to manually start the remote side.
#       TODO: It would be good to automatically map the ports in some way (2222 to 22 etc.), sync the buffer size etc., so the configuration on local and remote tunnel side are equal

import argparse
import logging
from carrier.mqtt import MqttCarrier, MqttConfig
from passenger.tcp import TcpPassenger, TcpPassengerConfig

def parse_args():
    parser = argparse.ArgumentParser(description="MQTT Tunnel")

    # General
    parser.add_argument("--role", required=True, choices=['local', 'remote'], help="Role of this tunnel end")

    # MQTT Config
    parser.add_argument("--mqtt-host", required=True, help="MQTT Broker Host")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT Broker Port")
    parser.add_argument("--mqtt-user", help="MQTT Username")
    parser.add_argument("--mqtt-pass", help="MQTT Password")
    parser.add_argument("--mqtt-ca-cert", help="MQTT Certificate path")
    parser.add_argument("--mqtt-qos", choices=[0, 1, 2], default=0, type=int, help="MQTT QoS")

    # TCP Config
    parser.add_argument("--tcp-port", type=int, required=True, help="Local TCP Listen Port")
    parser.add_argument("--tcp-buffer-size", default=65536, type=int, help="Buffer size of the TCP socket")

    return parser.parse_args()

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    args = parse_args()

    # Setup Configs
    mqtt_conf = MqttConfig(
        host=args.mqtt_host,
        port=args.mqtt_port,
        role=args.role,
        username=args.mqtt_user,
        password=args.mqtt_pass,
        ca_certs=args.mqtt_ca_cert,
        qos=args.mqtt_qos
    )
    tcp_conf = TcpPassengerConfig(
        port=args.tcp_port,
        role=args.role,
        buffer_size=args.tcp_buffer_size
    )

    # Instantiate
    carrier = MqttCarrier(config=mqtt_conf)
    passenger = TcpPassenger(carrier=carrier, config=tcp_conf)

    # Run
    try:
        passenger.run()
    except KeyboardInterrupt:
        logging.info("Stopping tunnel...")
        passenger.stop()

if __name__ == "__main__":
    main()
