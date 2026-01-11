import argparse
import logging
from carrier.mqtt import MqttCarrier, MqttConfig
from passenger.tcp import TcpPassenger, TcpPassengerConfig
from passenger.udp import UdpPassenger, UdpPassengerConfig

def parse_args():
    parser = argparse.ArgumentParser(description="MQTT Tunnel")

    # General
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose/debug logging")
    parser.add_argument("--role", required=True, choices=['local', 'remote'], help="Role of this tunnel end")

    # MQTT Config
    parser.add_argument("--mqtt-host", required=True, help="MQTT Broker Host")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT Broker Port")
    parser.add_argument("--mqtt-user", help="MQTT Username")
    parser.add_argument("--mqtt-pass", help="MQTT Password")
    parser.add_argument("--mqtt-ca-cert", help="MQTT Certificate path")
    parser.add_argument("--mqtt-qos", choices=[0, 1, 2], default=0, type=int, help="MQTT QoS")
    parser.add_argument("--mqtt-keep-alive-time", default=60, type=int, help="MQTT Keep Alive Time")
    parser.add_argument("--mqtt-topic", default="tunnel", type=str, help="Base topic for the tunnel (default: 'tunnel'). Will append /upstream and /downstream.")

    # TCP Config
    parser.add_argument("--tcp-port", type=int, required=False, help="Local TCP Listen Port")
    parser.add_argument("--tcp-buffer-size", default=65536, type=int, help="Buffer size of the TCP socket")

    # UDP Config
    parser.add_argument("--udp-listen-ip", type=str, default='0.0.0.0', help="UDP Listen IP")
    parser.add_argument("--udp-listen-port", type=int, required=False, help="UDP Listen Port")
    parser.add_argument("--udp-ip", type=str, default='127.0.0.1', help="UDP Destination IP")
    parser.add_argument("--udp-send-port", type=int, required=False, help="UDP connect to port")
    parser.add_argument("--buffer-size", default=65536, type=int, help="Buffer size of the TCP socket")

    return parser.parse_args()

def main():
    args = parse_args()

    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=logging_level,
        format=(
            "%(asctime)s | "
            "%(name)-15s | "
            "%(levelname)-7s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Setup Configs
    mqtt_conf = MqttConfig(
        host=args.mqtt_host,
        port=args.mqtt_port,
        role=args.role,
        username=args.mqtt_user,
        password=args.mqtt_pass,
        ca_certs=args.mqtt_ca_cert,
        qos=args.mqtt_qos,
        keep_alive_time=args.mqtt_keep_alive_time,
        topic=args.mqtt_topic
    )
    tcp_conf = TcpPassengerConfig(
        port=args.tcp_port,
        role=args.role,
        buffer_size=args.buffer_size
    )
    udp_conf = UdpPassengerConfig(
        listen_ip = args.udp_listen_ip,
        listen_port = args.udp_listen_port,
        send_ip = args.udp_ip,
        role=args.role,
        send_port = args.udp_send_port,
        buffer_size = args.buffer_size
    )

    # Instantiate
    carrier = MqttCarrier(config=mqtt_conf)
    passenger = UdpPassenger(carrier=carrier, config=udp_conf)

    # Run
    try:
        passenger.run()
    except KeyboardInterrupt:
        logger.info("Stopping via Keyboard Interrupt...")
        passenger.stop()

if __name__ == "__main__":
    main()
