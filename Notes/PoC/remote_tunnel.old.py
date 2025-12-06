import json
import socket
import paho.mqtt.client as mqtt
import threading

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

TARGET_HOST = "localhost"    # Ziel des Traffics
TARGET_PORT = 22             # Port des Zieldienstes (z.B. 22 für SSH, 80 für HTTP)
TOPIC_UP = "tunnel/c2s"      # Local -> Remote
TOPIC_DOWN = "tunnel/s2c"    # Remote -> Local

target_socket = None

def handle_target_responses(sock, m_client):
    """Liest Antworten vom SSH Server und schickt sie via MQTT zurück"""
    try:
        while True:
            data = sock.recv(4096) # Daten der eigenen Anwendung (z.B. SSH Client) lesen, 4096 Bytes als (gewöhnliche) Buffer-Größe, außreichend für viele Anwendungen (z.B. SSH)
            if not data:
                break
            m_client.publish(TOPIC_DOWN, data)
    except Exception as e:
        print(f"Fehler beim Lesen vom Target: {e}")
    finally:
        sock.close()
        print("Remote: Verbindung zum Target beendet.")

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    """Abboniert das Local -> Remote Topic nach Anmeldung beim Broker"""
    print(f"Remote: Verbunden mit Broker (Code {rc})")
    client.subscribe(TOPIC_UP)

def on_message(client, userdata, msg):
    """Schreibt eingehende MQTT Nachrichten in den lokalen TCP-Socket"""
    global target_socket

    if target_socket is None:
        try:
            print("Remote: Baue Verbindung zum Ziel-Dienst auf...")
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Socket zur Ziel-Anwendung auf dem Remote-Client (z.B. SSH)
            target_socket.connect((TARGET_HOST, TARGET_PORT)) # Baut aktive Verbindung mit dem Zielhost über entsprechenden Port auf (z.B. 22 für SSH)

            # Thread starten, der die ANTWORTEN vom Remote Ziel liest und verarbeitet (in MQTT Pakete packt und an den lokalen Client schickt)
            t = threading.Thread(target=handle_target_responses, args=(target_socket, client)) # Remote muss gleichzeitig lesen und schreiben: sock.recv(4096) wartet (eigentlich blockierend) auf Daten vom Zielhost, gleichzeitig könnten aber neue MQTT Nachrichten vom lokalen Client ankommen, die verarbeitet werden müssen. Daher darf recv hier nur auf einem eigenen Thread blockieren
            t.daemon = True
            t.start()
        except Exception as e:
            print(f"Remote: Fehler beim Verbinden zum Ziel: {e}")
            return

    # Daten nach dem Empfang von MQTT Nachrichten entpacken und über den eigenen TCP-Socket an das Ziel senden (z.B. an SSH im Remote Rechner selbst)
    try:
        target_socket.send(msg.payload)
    except Exception as e:
        print(f"Remote: Fehler beim Senden an Ziel: {e}")
        target_socket = None

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
mqtt_client.connect(BROKER_HOST, BROKER_PORT, 60)

print(f"Remote: Tunnel-Exit bereit. Leite weiter an {TARGET_HOST}:{TARGET_PORT}")
mqtt_client.loop_forever()
