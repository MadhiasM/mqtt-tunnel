import json
import socket
import paho.mqtt.client as mqtt

# KONFIGURATION
with open("config.json") as f:
    conf = json.load(f)

MODE = conf.get("connection_type", "wan")  # sichere Option als default

BROKER_HOST = conf["broker_host"]
USERNAME = conf["username"]
PASSWORD = conf["password"]
CA_PATH = conf["ca_path"]

# local access without TLS and Password Authentication via Port 1883
if MODE == "lan":
    BROKER_PORT = 1883
    USE_TLS = False
    USE_AUTH = False
# remote access with TLS and Password Authentication via Port 8883
elif MODE == "wan":
    BROKER_PORT = 8883
    USE_TLS = True
    USE_AUTH = True

else:
    raise ValueError(f"Invalid connection_type: {MODE}")

LOCAL_LISTEN_PORT = 2222     # SSH Verbindung wird über diesen Port geforwarded: ssh -p 2222 user@localhost
TOPIC_UP = "tunnel/c2s"      # Local -> Remote
TOPIC_DOWN = "tunnel/s2c"    # Remote -> Local

active_socket = None

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    """Abboniert das Remote -> Local Topic mit der Anmeldung beim Broker"""
    print(f"Lokal: Verbunden mit Broker (Code {rc})")
    client.subscribe(TOPIC_DOWN)

def on_message(client, userdata, msg):
    """Schreibt eingehende MQTT Nachrichten in den lokalen TCP-Socket"""
    global active_socket # Socket, über den die Payload an die Client-Anwendung (z.B. SSH) geschickt werden (nachdem sie über MQTT empfangen wurden und entpackt wurden)
    # Daten nach dem Empfang von MQTT Nachrichten entpacken und über den lokalen TCP-Socket an das Ziel senden (z.B. an SSH im Lokalen Rechner selbst)
    if active_socket:
        try:
            active_socket.send(msg.payload) # In MQTT gepackte Daten vom Remote-Ziel (z.B. SSH) kommen in der Payload an und werden hier über den active_socket an den SSH client weitergeleitet
        except Exception as e:
            print(f"Fehler beim Schreiben in Socket: {e}")

# MQTT Setup
mqtt_client = mqtt.Client()
if USE_AUTH:
    mqtt_client.username_pw_set(USERNAME, PASSWORD)
if USE_TLS:
    mqtt_client.tls_set(
        ca_certs=CA_PATH,
        certfile=None,
        keyfile=None
    )
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER_HOST, BROKER_PORT, 60) # Verbindung mit Broker über MQTT Port 1883 oder 8883 mit Keepalive Time
mqtt_client.loop_start() # Hintergrund-Thread für MQTT, daher kein separates Threading notwendig und recv kann blockierend aufgerufen werden

# TCP Server Setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # erstellt Socket: AF_INET: IPv4, SOCK_STREAM = TCP (verbindungsorientiert)
server.bind(("0.0.0.0", LOCAL_LISTEN_PORT)) # Bindet Socket an alle Netzwerkschnittstellen des Rechners (0.0.0.0) und den Port LOCAL_LISTEN_PORT (z. B. 2222). Andere Programme können sich via localhost:LOCAL_LISTEN_PORT verbinden.
server.listen(1) # Listening-Modus, um eingehende Verbindungen zu akzeptieren (maximale eine gleichzeitig wartende Verbindung)

print(f"Lokal: Tunnel bereit auf Port {LOCAL_LISTEN_PORT}. Warte auf Verbindung...")

try:
    while True:
        client_sock, addr = server.accept() # Wartet, bis ein Client sich verbindet. (also z.B. auf 'ssh -p 2222 user@localhost') und gibt das Socket Objekt und die Client-Adresse zurück
        print(f"Lokal: Neue Verbindung von {addr}")
        active_socket = client_sock # Speicher Verbindung global, sodass über on_message Daten über diese Verbindung geschickt werden können

        while True:
            data = client_sock.recv(4096) # Daten der eigenen Anwendung (z.B. SSH Client) lesen, 4096 Bytes als (gewöhnliche) Buffer-Größe, sollte für SSH ausreichen
            if not data:
                break
            mqtt_client.publish(TOPIC_UP, data) # In MQTT verpacken und senden

        client_sock.close()
        print("Lokal: Verbindung geschlossen.")
        active_socket = None
except KeyboardInterrupt:
    server.close()
    mqtt_client.loop_stop()
