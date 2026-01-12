# MQTT Tunnel

A TCP/UDP tunnel, which uses MQTT.

Allowing you to expose services through an MQTT broker. Perfect for scenarios where direct connections aren't possible but both endpoints can reach an MQTT broker.

## Features

- Bidirectional tunneling of TCP or UDP traffic over MQTT
- Support for TLS/SSL connections to MQTT broker

## How It Works

```
[Local Service] <--TCP/UDP--> [Local Tunnel] <--MQTT--> [Remote Tunnel] <--TCP/UDP--> [Remote Service]
```

The tunnel consists of two components:
- **Local**: Listens for incoming connections and forwards traffic to MQTT
- **Remote**: Receives MQTT messages and forwards them to the destination service

## Installation

```bash
git clone https://github.com/MadhiasM/mqtt-tunnel.git
cd mqtt-tunnel
python3 -m venv venv
source venv/bin/activate
pip install paho-mqtt
```

## Usage

### Basic TCP Tunnel

**Local side** (listens on port 8000):
```bash
python3 main.py --role local --mqtt-host broker.example.com --listen-port 8000
```

**Remote side** (forwards to localhost:22):
```bash
python3 main.py --role remote --mqtt-host broker.example.com --dst-ip 127.0.0.1 --dst-port 22
```
For udp just add `-u` flag.

## Command Line Options

### General Options
- `--role` - Role of this tunnel end (`local` or `remote`) [required]
- `-u` - Use UDP instead of TCP
- `-v, --verbose` - Enable verbose/debug logging

### MQTT Options
- `--mqtt-host` - MQTT broker hostname or IP [required]
- `--mqtt-port` - MQTT broker port (default: 1883)
- `--mqtt-user` - MQTT username
- `--mqtt-pass` - MQTT password
- `--mqtt-ca-cert` - Path to CA certificate for TLS
- `--mqtt-qos` - MQTT QoS level (0, 1, or 2; default: 0)
- `--mqtt-keep-alive-time` - Keep alive time in seconds (default: 60)
- `--mqtt-topic` - Base topic for the tunnel (default: "tunnel")

### Tunnel Options
- `--listen-port` - Port to listen on (local role)
- `--listen-ip` - IP address to listen on (default: 0.0.0.0)
- `--dst-ip` - Destination IP address (remote role; default: 127.0.0.1)
- `--dst-port` - Destination port (remote role)
- `--buffer-size` - Socket buffer size in bytes (default: 65536)

## Examples

### SSH over MQTT
Forward SSH connections through an MQTT broker:

**Local machine**:
```bash
python3 main.py --role local --mqtt-host mqtt.example.com --listen-port 2222
```

**Remote machine** (with SSH server on port 22):
```bash
python3 main.py --role remote --mqtt-host mqtt.example.com --dst-port 22
```

Connect to SSH:
```bash
ssh -p 2222 user@localhost
```