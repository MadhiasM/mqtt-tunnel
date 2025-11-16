# mqtt-tunnel

Team: Robert, Lars, Mathias

## Planung
### Analyse
#### Organisation
- [ ] Rollenverteilung: Leitung, Architektur, Implementierung, Testing, ...
- Zu klärende Fragen:
  - Was brauchen wir server-/clientseitig, welche Libraries, ...
  - welche Funktionen/Methoden/... brauchen wir - danach dann Aufteilung der Arbeitspakete 
  - Welche MQTT Funktionen (QoS, Retained Messages, ...) wollen wir nutzen? (Latenz durch ACK, ...)
  - Zusammenspiel TCP und MQTT
    - Paketreihenfolge? QoS 2: https://www.echolon.de/de/blog/das-mqtt-protokoll-im-iot/ Wieso sollte das so sein? https://stackoverflow.com/questions/30955110/is-message-order-preserved-in-mqtt-messages, https://drdroid.io/stack-diagnosis/mqtt-messages-are-not-being-delivered-in-the-order-they-were-sent - möglicherweise nicht direkt in MQTT sondern in TCP? https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.pdf "The protocol runs over TCP/IP, or over other network protocols that provide ordered, lossless, bidirectional connections."
- Server:
  - Welcher MQTT Broker
- Welcher Client

- 25./26.11. nächstes Sync
- 31.12. Umsetzung Tunnel, dann Testing + Dokumentation
- 16.01. Abgabe schriftliche Ausarbeitung + Code
- 31.01. Vortrag
  

- [X] Kommunikationskanal: [Discord](https://discord.com/channels/@me/1424823853447905312)
- [x] VCS + Hosting: [GitHub](https://github.com/MadhiasM/mqtt-tunnel)
#### Anforderungen
- siehe [Moodle](https://moodle.fernuni-hagen.de/course/section.php?id=35887)

- [ ] Tunnel sollte Protokoll verwenden, das trotz Firewalling / Proxies verfügbar ist
  - Wie verbreitet ist das Protokoll?
  - Sind die genutzten Ports in bestimmten Umgebungen freigeschaltet?
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

#### Trägerprotokollauswahl (Tunnel) (carrier)
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
  - potentielle Use Cases:
    - Universaler Transportkanal für Geräte und Standorte, die im Internet nicht erreichbar sind — aber einen MQTT-Broker erreichen können.
    - MQTT ist weltweit in IoT, Automatisierung, industriellen Anlagen, Logistik, Smart Home und Embedded Systemen verbreitet, in bestimmten Umfeldern eines der wenigen Protokolle, das nicht blockiert wird.

    - Use Case A — Fernwartung von IoT-Geräten hinter Firewalls
      - Viele IoT-Geräte sitzen hinter strengen Unternehmens-Firewalls oder Mobilfunknetzen (NAT, CGNAT). SSH, HTTPS oder VPN funktionieren nicht.
      - MQTT ermöglicht es, Logs zu ziehen, Diagnosen durchführen, OTA-Updates einzuspielen, da MQTT in all diesen Netzen fast immer offen ist, der MQTT-Tunnel ermöglicht „SSH durch MQTT“, also remote Zugriff ohne Port-Freigaben, ohne VPN, ohne Reverse SSH Hacks. Manche Geräte ermöglichen nur die Kommunikation über MQTT
      - Zielkunden: Maschinenbauer, Hersteller von Embedded-Systemen, Smart-Home-Gerätehersteller, Gateway-Hersteller (LTE, 5G, NB-IoT)
    - Use Case B — Sichere Kommunikation über Mobilfunknetze, in denen alles andere geblockt ist
      - Einige Mobilfunkanbieter erlauben MQTT (Standard-Port 8883 / 443 via WS) und HTTP/HTTPS, aber blockieren eingehende Verbindungen, viele Ports, VPN-Protokolle (IPsec, WireGuard, OpenVPN), der MQTT-Tunnel arbeitet nur ausgehend, über eine einzige persistente Verbindung zum Broker.
      - Zielkunden: Logistik (Truck Gateways), Energieversorger, Smart Meter Hersteller, Fahrzeuge/Flotten, Outdoor-Sensorik
    - Use Case C — Sichere Datenübertragung in Ländern mit starkem Firewalling / Zensur
      - In restriktiven Netzwerken (Hotel-WLAN, Firmennetze, bestimmte Länder, Flugzeuge) sind sehr viele Protokolle blockiert. MQTT-over-WebSocket-over-TLS:443 ist kaum unterscheidbar von HTTPS.
      - Ein MQTT-Tunnel ermöglicht: VPN-ähnliche Verbindungen, HTTP-Zugriff, Dateiübertragung selbst in restriktiven Netzen.
      - Zielkunden: NGOs, Unternehmen mit internationalen Niederlassungen, Journalistenausrüstung, Touristen

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

#### Nutzprotokollauswahl (getunnelt) (passenger)
- TCP Pakete sind kleiner als max. MQTT Message Größe, daher keine erneute Aufteilung nötig
- 

### Architektur & Design
- MQTT Pakete mithilfe der bestehenden Libraries hin und her schicken
- Dann an TUN Devices weitergeben
### Implementierung

### Test & Validierung

### Dokumentation
