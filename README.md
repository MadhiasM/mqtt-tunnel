# mqtt-tunnel

Team: Robert, Lars, Mathias
## Planung
### Organisation
- [ ] Rollenverteilung: Arbeitspakete, Architektur, Implementierung, Testing, ...
- [X] Kommunikationskanal: [Discord](https://discord.com/channels/@me/1424823853447905312)
- [x] VCS + Hosting: [GitHub](https://github.com/MadhiasM/mqtt-tunnel)

- 25./26.11. nächster Sync
- 31.12. Umsetzung Tunnel, dann Testing + Dokumentation bis zur Abgabe
- 16.01. Abgabe schriftliche Ausarbeitung + Code
- 31.01. Vortrag^
### offene Fragen
  - **MQTT**:
    - [ ] Server/**Broker**: Mosquitto? 
    - [ ] **Client**: Paho (Python, Go, C), rumqtt (Rust), HiveMQ (Java), FastAPI? (Python), MQTT-C (C)
  - Funktionen/Methoden/... brauchen wir - danach dann Aufteilung der Arbeitspakete 
  - Welche **MQTT Features** (QoS, Retained Messages, ...) wollen wir nutzen? (Latenz durch ACK, ...)
  - Zusammenspiel TCP und MQTT: Sequencing/Paketreihenfolge? Eigene Implementierung notwendig?
    - https://www.hivemq.com/blog/understanding-mqtt-message-ordering/ "MQTT 3.1.1 guarantees that for a single connection, the broker will deliver messages in the order they are received for each subscribed topic, respecting the QoS level: "A Server MUST by default treat each Topic as an ”Ordered Topic”. [...] However, this does not apply across different topics or different connections. [...] If both Client and Server make sure that no more than one message is “in-flight” at any one time (by not sending a message until its predecessor has been acknowledged), then no QoS 1 message will be received after any later one. For example, a subscriber might receive them in the order 1,2,3,3,4 but not 1,2,3,2,3,4. Setting an in-flight window of 1 also means that order will be preserved even if the publisher sends a sequence of messages with different MQTT QoS levels on the same topic.”"
    - https://www.echolon.de/de/blog/das-mqtt-protokoll-im-iot/ QoS 2 Wieso sollte das so sein? "QoS 2 stellt sicher, dass die Nachrichten genau einmal und in der richtigen Reihenfolge übertragen werden, erfordert jedoch mehr Bandbreite und Rechenleistung." Begründung?
    - https://stackoverflow.com/questions/30955110/is-message-order-preserved-in-mqtt-messages
    - https://drdroid.io/stack-diagnosis/mqtt-messages-are-not-being-delivered-in-the-order-they-were-sent - möglicherweise nicht direkt in MQTT sondern in TCP? 
    - https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.pdf "The protocol runs over TCP/IP, or over other network protocols that provide ordered, lossless, bidirectional connections."
- **TCP Meltdown** (TCP over TCP): MQTT nutzt TCP, tunnelt aber in der Payload nochmals TCP; potentielles Risiko und Performancekiller [Link1](https://openvpn.net/as-docs/faq-tcp-meltdown.html), [Link2](https://www.youtube.com/watch?v=AAssk2N_oPk), [Link3](https://serverfault.com/questions/1045786/what-is-tcp-over-tcp-and-how-does-openvpn-under-tcp-mode-avoid-the-issue)
  - **getunneltes** Protokoll: TCP, UDP, IP, HTTP(S)? 
## Analyse
### Anforderungen
- siehe [Moodle](https://moodle.fernuni-hagen.de/course/section.php?id=35887)

- [ ] Tunnel sollte Protokoll verwenden, das trotz Firewalling / Proxies verfügbar ist
  - Wie verbreitet ist das Protokoll? MQTT.
  - Sind die genutzten Ports in bestimmten Umgebungen freigeschaltet? MQTT.
- [ ] mindestens einen Tunnel implementieren, wie HTTP(S), optional allgemeine TCP-Verbindungen (z. B. SSH, WireGuard)
  - Erster Ansatz: Allgemeiner IP (TCP/UDP) Tunnel, ermöglicht auch DNS Anfragen
- [ ] mit vorhandenen Libraries implementierbar sein, sodass der Projektrahmen nicht gesprengt wird, einfaches und effizientes Debugging möglich ist

1. [ ] Erörtern Sie, welches Protokoll Ihr Trägerprotokoll wird.
	- Broker-Basiertes Protokoll, wo es bisher noch nicht so viele Lösungen gibt:
		- [ ] Warum MQTT? Verbreitung, Firewallumgehung möglich, Libraries, ...
		- [ ] Zuhilfenahme von Tools/Frameworks explizit empfohlen
2. [ ] Erörtern Sie, ob Sie allgemein alle TCP oder UDP oder IP-Verbindungen tunneln wollen, oder nur HTTP(S).
	- [ ] Welche Protokolle werden getunnelt?
		- [ ] Idealfall: alles weitere mittels SSH, OpenVPN oder Wireguard durchtunneln
		- [ ] Alternativ: Nur HTTP(s) Anfragen tunneln
		- [ ] Muss begründet werden
3. [ ] Implementieren Sie Ihren Tunnel. Dokumentieren Sie Implementationsentscheidungen.
	- Hinweis: Dazu sollten Sie auch die Anforderungen und Lösungsideen gründlich analysieren, der Anspruch ist, daß die Beschreibung zwar abstrakt, aber konkret genug ist, daß auf Ihr Darstellung aufbauend jemand die Implementierung erfolgreich starten kann. Der Teufel liegt bekanntlich im Detail, das vielleicht auch erst bei Tests und der Umsetzung auffällt, das müssen Sie nicht entdecken. Die Ergebnisse sollten sich in Ihrem Paper wiederfinden.

4. [ ] Testen Sie Ihren Tunnel gründlich. Dazu gehört auch, den Tunnel mal mit tcpdump, Wireshark o.ä. aufzuzeichnen und zu prüfen, was ein Dritter sieht.

5. [ ] Dokumentieren Sie in Ihrer Abgabe, welche Gruppenmitglieder an welchem Teil der Aufgabe mitgewirkt haben, wer für welchen Teil "den Hut auf hatte" und welchen Anteil welches Gruppenmitglied an dem Teil hatte. Im Idealfall sollten im Ergebnis alle Gruppenmitglieder etwa gleich viel geleistet haben.
### Trägerprotokollauswahl (Tunnel/carrier)
[Carrier und Passanger Protokolle](https://tsbates.com/blog/transport-vs-carrier-vs-passenger-protocols/)
- [MQTT](https://github.com/mqtt/mqtt.org)
  - **Quality of Service** (QoS) bietet die Möglichkeit, verschiedene Anforderungen an garantierte Zustellung zu erfüllen, je nach Bedarf
  - **Retained Messages** bietet die Möglichkeit, die letzte Nachricht eines Topics auf dem Broker zu speichern. Dadurch erhalten neue Client direkt den letzten Status, ohne auf eine Aktualisierung warten zu müssen
  - **Last Will Testament** bietet die Möglichkeit, Abonennten mit einer Nachricht zu informieren, wenn ein Gerät die Verbindung verliert.
  - Implementierungsaufwand machbar für den Umfang eines Fachpraktikums: Tools/Frameworks/Libraries bereits vorhanden (Broker: Mosquitto, EMQX, NanoMQ, Cloud Based Brokers; Client-side Frameworks: Paho, FastAPI, HiveMQ, Objective-C MQTT-Client Framework; WebFrameworks: Express.js)
  - allgemeiner Use Case: schlechte Netzwerke, instabile Verbindungen, NAT / Firewall Beschränkungen
    - Broker stabilisiert Verbindungen (Session, Keepalive, Retain, QoS)
    - Pub/Sub entkoppelt Sender und Empfänger
  - kein High-Throughput, low-latency System
  - Beliebiger Datendurchsatz möglich, da Binärdaten erlaubt sind
  - Firewall / Proxy Toleranz
    - Nutzt TCP:1883/8883, oftmals geblockt
    - MQTT over WebSockets läuft über Port 443, fast immer offen, höchste Wahrscheinlichkeit der Verfügbarkeit
  - Umsetzbarkeit
    - HTTP: einfach
    - TCP-Streams: machbar über Topics + Sequencing
    - SSH/WireGuard: möglich, aber nicht super effizient, für ein Praktikum aber demonstrierbar
  - potentieller Use Case:
    - Universaler Transportkanal für Geräte und Standorte, die im Internet nicht erreichbar sind, aber einen MQTT-Broker erreichen können.
    - MQTT ist weltweit in IoT, Automatisierung, industriellen Anlagen, Logistik, Smart Home und Embedded Systemen verbreitet, in bestimmten Umfeldern eines der wenigen Protokolle, das nicht blockiert wird.

- [NATS](https://github.com/nats-io/nats-server)
  - 40 Client language Implenmentierungen
  - Server kann on premise, in der Cloud, auf einem Raspberry Pi oder sogar auf Edge-Geräten laufen
  - kein QoS, aber Persistenz und Reihenfolgegarantie über JetStream (Overhead) möglich
  - High-Throughput, low-latency
  - weniger Dokumentation, mehr Grundlagenarbeit notwendig
  - Firewall / Proxy Toleranz
    - TCP:4222 → meist blockiert
    - WebSocket-Gateway (optional): Port 443 möglich, aber weniger standardmäßig implementiert, weniger verbreitet, keine geeigneten Frameworks
  - Signifikatester Vorteil über MQTT: Performance (Throughput/Latency) überwiegt nicht die Nachteile (Firewall Toleranz, Frameworks, Dokumentation, Implementierbarkeit)
- CORBA
  - Verbreitung nicht mit MQTT vergleichbar, daher nicht so gut zur Firewallumgehung geeignet
  - Legacy Industrie-/Telekommunikations- oder Militärsysteme
  - Technisch anspruchsvoll
  - keine Frameworks, Setup mühsam
- AMQP
  - Komplexere Routing-Mechanismen
  - Ausfallsicherheit / garantierte Zustellung durch persistente Queues und ACK-Systeme.
  - Transaktionale Anwendungen wie Banking (Echtzeitüberweisung, Hochfrequenztrading), nicht notwendig für dieses Projekt
  - Vorteil der nahtlosen Integration in Enterprise-Umgebungen (SAP, Oracle) über standardisierte Schnittstellen bietet in diesem Projekt keinen Mehrwert

Quellen:
https://www.newroom-media.de/blog/mqtt-coap-amqp-welches-iot-protokoll-eignet-sich-fuer-dein-projekt/
### Nutzprotokollauswahl (getunnelt/passenger)
- TCP Pakete sind kleiner als max. MQTT Message Größe, daher keine erneute Aufteilung nötig

## Architektur & Design
- MQTT Pakete mithilfe der bestehenden Libraries hin und her schicken
- Dann an TUN Devices weitergeben

## Implementierung

## Test & Validierung

## Dokumentation & Präsentation
