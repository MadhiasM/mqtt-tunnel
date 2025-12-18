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
    parser.add_argument("--mqtt-keep-alive-time", default=60, type=int, help="MQTT Keep Alive Time")

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
        qos=args.mqtt_qos,
        keep_alive_time=args.mqtt_keep_alive_time
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
