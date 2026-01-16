# MQTT Tunnel

> A TCP/UDP tunnel over MQTT for exposing services through an MQTT broker

Perfect for scenarios where direct connections aren't possible but both endpoints can reach an MQTT broker. In combination with SSH/Wireguard it is possible to tunnel a full VPN. Does not support IPv6!

---

##  Features

-  Bidirectional tunneling of TCP or UDP traffic over MQTT
-  Support for TLS/SSL connections to MQTT broker

---

##  How It Works

```
[Local Service] <--TCP/UDP--> [Local Tunnel] <--MQTT--> [Remote Tunnel] <--TCP/UDP--> [Remote Service]
```

The tunnel consists of two components:

| Component | Description |
|-----------|-------------|
| **Local** | Listens for incoming connections and forwards traffic to MQTT |
| **Remote** | Receives MQTT messages and forwards them to the destination service |

---
## Requirements

- Python >= 3.8
- paho-mqtt >= 2.0

##  Installation

```bash
git clone https://github.com/MadhiasM/mqtt-tunnel.git
cd mqtt-tunnel
python3 -m venv venv
source venv/bin/activate
pip install paho-mqtt
```

---

##  Usage

### Basic TCP Tunnel

**Local side** (listens on port 8000):
```bash
python3 main.py --role local --mqtt-host broker.example.com \
  --listen-port 8000
```

**Remote side** (forwards to localhost:22):
```bash
python3 main.py --role remote --mqtt-host broker.example.com \
  --dst-ip 127.0.0.1 --dst-port 22
```

> **Note:** For UDP just add the `-u` flag.

---

##  Command Line Options

### General Options

| Option | Description |
|--------|-------------|
| `--role` | Role of this tunnel end (`local` or `remote`) **[required]** |
| `-u` | Use UDP instead of TCP |
| `-v, --verbose` | Enable verbose/debug logging |

### MQTT Options

| Option | Default | Description |
|--------|---------|-------------|
| `--mqtt-host` | - | MQTT broker hostname or IP **[required]** |
| `--mqtt-port` | `1883` | MQTT broker port |
| `--mqtt-user` | - | MQTT username |
| `--mqtt-pass` | - | MQTT password |
| `--mqtt-ca-cert` | - | Path to CA certificate for TLS |
| `--mqtt-qos` | `0` | MQTT QoS level (0, 1, or 2) |
| `--mqtt-keep-alive-time` | `60` | Keep alive time in seconds |
| `--mqtt-max-msg-size` | `268435456` | Message size limit for MQTT payloads |
| `--mqtt-topic` | `tunnel` | Base topic for the tunnel |
| `--mqtt-transport` | `tcp` | Transport (tcp or websockets) |
| `--mqtt-ws-path` | `/mqtt` | MQTT WebSocket path |
| `--mqtt-tls-allow-insecure` | `False` | Disable TLS certificate verification |

### Tunnel Options

| Option | Default | Description |
|--------|---------|-------------|
| `--listen-port` | - | Port to listen on (local role) |
| `--listen-ip` | `0.0.0.0` | IP address to listen on |
| `--dst-ip` | `127.0.0.1` | Destination IP address (remote role) |
| `--dst-port` | `22` | Destination port (remote role) |
| `--buffer-size` | `65536` | Socket buffer size in bytes |

---

---

##  Examples

### SSH over MQTT

Forward SSH connections through an MQTT broker.

#### Setup

**Local machine:**
```bash
python3 main.py --role local --mqtt-host mqtt.example.com --listen-port 2222
```

**Remote machine** (with SSH server on port 22):
```bash
python3 main.py --role remote --mqtt-host mqtt.example.com --dst-port 22
```

#### Connect

```bash
ssh -p 2222 user@localhost
```

---

### VPN: Full IP Tunnel using SSH

#### Step 1: Prepare SSH Server

```bash
sudo ip tuntap add dev tun0 mode tun
sudo ip addr add 10.0.0.1/24 dev tun0
sudo ip link set up dev tun0
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
```

Start MQTT-Tunnel (Server-Side):

```bash
python3 main.py --role remote --mqtt-host mqtt.example.com
```

#### Step 2: Prepare SSH Client

```bash
sudo ip tuntap add dev tun0 mode tun
sudo ip link set tun0 up
sudo ip addr add 10.0.0.2/24 dev tun0
sudo ip route add default via 10.0.0.1
```

Setup route to MQTT Server *(necessary if MQTT Server is not in local subnet)*:

```bash
sudo ip route add IP_of_MQTT_server/32 via GATEWAY_IP 
sudo ip route add default via 10.0.0.1 dev tun0
```

Start MQTT-Tunnel (Client-Side):

```bash
python3 main.py --mqtt-host IP_of_MQTT_server --role local --listen-port 8000
```

#### Step 3: Connect via SSH

```bash
ssh -p 8000 -w 0:0 user@localhost
```

If you use IPv6 you may want to disable it to prevent leakage:

```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
```

---

### VPN: Using Wireguard

#### Step 1: Configure PeerA (Server)

**`/etc/wireguard/wgA.conf`**
```ini
[Interface]
PrivateKey = PRIVATE_KEY_PEER_A
Address = 10.0.0.1/24
ListenPort = 51820  

[Peer]
PublicKey = PUBLIC_KEY_PEER_B
AllowedIPs = 10.0.0.2/32
Endpoint = 127.0.0.1:5000  
PersistentKeepalive = 25
```

#### Step 2: Configure PeerB (Client)

**`/etc/wireguard/wgB.conf`**
```ini
[Interface]  
PrivateKey = PRIVATE_KEY_PEER_A
Address = 10.0.0.2/24  
  
[Peer]  
PublicKey = PUBLIC_KEY_PEER_B
AllowedIPs = 10.0.0.0/24  
Endpoint = 127.0.0.1:8000  
PersistentKeepalive = 25
```

#### Step 3: Setup PeerA (Server)

Setup IP forwarding and iptables:

```bash
sudo sysctl -w net.ipv4.ip_forward=1

sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o YOUR_NETWORK_DEVICE -j MASQUERADE
sudo iptables -A FORWARD -i wg0 -j ACCEPT
sudo iptables -A FORWARD -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -I FORWARD 1 -i wg0 -o YOUR_NETWORK_DEVICE -j ACCEPT
sudo iptables -I FORWARD 2 -i YOUR_NETWORK_DEVICE -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT

sudo wg-quick up wgA
```

Start MQTT-Tunnel:

```bash
python3 main.py -u --mqtt-host mqtt.example.com --role remote --udp-send-port 51820
```

#### Step 4: Setup PeerB (Client)

Add explicit route to MQTT Server:

```bash
sudo ip route add IP_of_MQTT_server/32 via GATEWAY_IP
```

Start Wireguard:

```bash
sudo wg-quick up wgB
```

If you use IPv6 you may want to disable it to prevent leakage:

```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
```
> Wireguard sets up the routing automatically.

___

### Forward a SOCKS proxy through an MQTT broker.

Forward SSH connections through an MQTT broker.

#### Setup

**Local machine:**
```bash
python3 main.py --role local --mqtt-host mqtt.example.com --listen-port 2222
```

**Remote machine** (with SSH server on port 22):
```bash
python3 main.py --role remote --mqtt-host mqtt.example.com --dst-port 22
```

#### Connect

```bash
ssh -D 1234 user@localhost -p 2222 -v
```

#### Configure SOCKS Proxy in browser or system

Configure SOCKS Proxy in system or browser: Host: `localhost` Port: `1234`