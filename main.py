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
    parser.add_argument("-u", action='store_true', help="Use UDP instead of TCP")
    

    # MQTT Config
    parser.add_argument("--mqtt-host", required=True, help="MQTT Broker Host")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT Broker Port")
    parser.add_argument("--mqtt-user", help="MQTT Username")
    parser.add_argument("--mqtt-pass", help="MQTT Password")
    parser.add_argument("--mqtt-ca-cert", help="MQTT Certificate path")
    parser.add_argument("--mqtt-qos", choices=[0, 1, 2], default=0, type=int, help="MQTT QoS")
    parser.add_argument("--mqtt-keep-alive-time", default=60, type=int, help="MQTT Keep Alive Time")
    parser.add_argument("--mqtt-topic", default="tunnel", type=str, help="Base topic for the tunnel (default: 'tunnel'). Will append /upstream and /downstream.")
    parser.add_argument("--mqtt-transport", choices=["tcp", "websockets"], default="tcp", help="Transport mechanism (default: tcp)")
    parser.add_argument("--mqtt-ws-path", default="/mqtt", help="MQTT WebSocket path (default: /mqtt")
    parser.add_argument("--mqtt-tls-allow-insecure", default=False, help="Allow TLS connections without verifying the server name matches the certificate label.")

    # TCP Config
    parser.add_argument("--listen-port", type=int, required=False, help="Local Listen Port")

    # UDP Config
    parser.add_argument("--listen-ip", type=str, default='0.0.0.0', help="UDP Listen IP")
    parser.add_argument("--dst-ip", type=str, default='127.0.0.1', help="Destination IP")
    parser.add_argument("--dst-port", type=int, required=False, help="Destination Port")
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
        topic=args.mqtt_topic,
        transport=args.mqtt_transport,
        ws_path=args.mqtt_ws_path,
        tls_allow_insecure= args.mqtt_tls_allow_insecure
    )

    tcp_conf = TcpPassengerConfig(
        role=args.role,
        listen_ip = args.listen_ip,
        listen_port = args.listen_port,
        dst_ip = args.dst_ip,
        dst_port = args.dst_port,
        buffer_size = args.buffer_size,
    )
    udp_conf = UdpPassengerConfig(
        role=args.role,
        listen_ip = args.listen_ip,
        listen_port = args.listen_port,
        dst_ip = args.dst_ip,
        dst_port = args.dst_port,
        buffer_size = args.buffer_size,
    )

    # Instantiate
    carrier = MqttCarrier(config=mqtt_conf)
    if args.u:
        passenger = UdpPassenger(carrier=carrier, config=udp_conf)
    else:
        passenger = TcpPassenger(carrier=carrier, config=tcp_conf)

    # Run
    try:
        passenger.run()
    except KeyboardInterrupt:
        logger.info("Stopping via Keyboard Interrupt...")
        passenger.stop()

if __name__ == "__main__":
    main()
