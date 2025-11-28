# mqtt-tunnel
## Projektstatus
**Team:** Robert, Lars, Mathias 
**Kommunikation:** [Discord](https://discord.com/channels/@me/1424823853447905312) 
**Repo:** [GitHub](https://github.com/MadhiasM/mqtt-tunnel)
## Zeitplan & Orga
- **31.12.:** Umsetzung Tunnel
- **Januar:** Testing, Dokumentation, Feinschliff
- **16.01.:** Abgabe (Schriftliche Ausarbeitung + Code)
- **31.01.:** Vortrag
___
## Next Steps (Ziel: 1 Woche)

**Mathias**
- [ ] Übrige Einsendeaufgaben durch den MQTT Tunnel (SOCKS) jagen.
- [ ] **TUN** VPN (IP-Tunnel) direkt implementieren (SSH-Layer entfernen).
- [ ] Instabile Verbindungen simulieren (Mobile Daten).
- [ ] Buffer Size massiv hochdrehen.
**Robert**
- [ ] Latenzanalyse durchführen (Einfluss von Packet/Message/Buffer Size Limits).
**Lars**
- [ ] Analyse von `max_inflight_bytes` / `messages` und QoS-Settings auf den Durchsatz.
**Gemeinsam**
- [ ] Dokumentation der Implementierungsentscheidungen für das Paper fortführen.
___
___
## Anforderungen
- siehe [Moodle](https://moodle.fernuni-hagen.de/course/section.php?id=35887)

- [x] Tunnel sollte Protokoll verwenden, das trotz Firewalling / Proxies verfügbar ist
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
___
## Analyse
### Trägerprotokoll (Carrier): MQTT
- [ ] **Gründe:** Hohe Verbreitung, sehr gute Firewall-Toleranz (Port 443 via WebSockets oft offen), existierende Frameworks (Mosquitto, Paho), wodurch ohne viel Overhead oder eigene Low-Level Implementierungen ein Proof of Concept machbar ist.
	- [ ] TODO: Aktuell nur Port 1883 und 8883. Variante über WebSockets mit Port 443
- **Features:**
    - _QoS:_ Ermöglicht Steuerung von Latenz vs. Zustellgarantie.
    - _Last Will / Testament & Birth Message:_ Zur Überwachung der Verbindungsstabilität (Robustheit).
    - _Retained Messages:_ Status-Updates für neue Clients.
    - Auch bei instabilen Verbindungen nutzbar über Funktionen _Session_, _Keepalive_, _Retain_, _QoS_
    - Pub/Sub entkoppelt Sender und Empfänger
- **weitere Eigenschaften**:
	- viele Libraries für Broker und Client
	- ausführliche, aber leicht verständliche Dokumentation 
	- Beliebiger Datendurchsatz möglich, da Binärdaten erlaubt sind
- [ ] TODO: **Message Order Preservation** 
	-  [Unterstanding MQTT Message Ordering](https://www.hivemq.com/blog/understanding-mqtt-message-ordering/), 
		- "MQTT 3.1.1 guarantees that for a single connection, the broker will deliver messages in the order they are received for each subscribed topic, respecting the QoS level: "A Server MUST by default treat each Topic as an ”Ordered Topic”. [...] However, this does not apply across different topics or different connections. [...] If both Client and Server make sure that no more than one message is “in-flight” at any one time (by not sending a message until its predecessor has been acknowledged), then no QoS 1 message will be received after any later one. For example, a subscriber might receive them in the order 1,2,3,3,4 but not 1,2,3,2,3,4. Setting an in-flight window of 1 also means that order will be preserved even if the publisher sends a sequence of messages with different MQTT QoS levels on the same topic.”"
	-   [Das MQTT Protokoll im IOT](https://www.echolon.de/de/blog/das-mqtt-protokoll-im-iot/)
		- "QoS 2 stellt sicher, dass die Nachrichten genau einmal und in der richtigen Reihenfolge übertragen werden, erfordert jedoch mehr Bandbreite und Rechenleistung." Begründung?
	-  [Is message order preserved in MQTT messages?](https://stackoverflow.com/questions/30955110/is-message-order-preserved-in-mqtt-messages)
		- "- QoS 0 messages will be delivered in order (albeit messages may get lost). QoS 2 messages will be delivered in order. QoS 1 allows for message duplicates - it is possible a duplicate will arrive _after_ the first instance of the next message that was published. QoS 1 ordering can be guaranteed if the client/broker only allow a single message inflight at any time. -
	- [MQTT Messages are not being delivered in the order they were sent.](https://drdroid.io/stack-diagnosis/mqtt-messages-are-not-being-delivered-in-the-order-they-were-sent)
		- "For preserving message order, using QoS 1 or QoS 2 is recommended.", "Some brokers, like [Eclipse Mosquitto](https://www.eclipse.org/paho/), support ordered message delivery by default, but it's essential to verify the settings."
		- "Ensure that both the publisher and subscriber are using the same QoS level to maintain order." 
	- [MQTT 3.1.1.1 Documentation](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718105) oder [MQTT 5.0 Documentation](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901240)
		-  Abstract: "The protocol runs over TCP/IP, or over other network protocols that provide ordered, lossless, bi-directional connections.", Abstract; 
		- Abschnitt 4.6 Message Ordering: 
			- "A Server MUST treat every, Topic as an Ordered Topic when it is forwarding messages on Non‑shared Subscriptions."
			- "When a Server processes a message that has been published to an Ordered Topic, it MUST send PUBLISH packets to consumers (for the same Topic and QoS) in the order that they were received from any given Client."
			- "If both Client and Server set Receive Maximum to 1, they make sure that no more than one message is “in-flight” at any one time."
			- [ ] "If both Client and Server set Receive Maximum to 1, they make sure that no more than one message is “in-flight” at any one time. In this case no QoS 1 message will be received after any later one even on re-connection. For example a subscriber might receive them in the order 1,2,3,3,4 but not 1,2,3,2,3,4."

	- **Bottomline**: 
		- MQTT garantiert für eine _einzelne Verbindung_ und ein _einzelnes Topic_, dass der Broker die Nachrichten in der Reihenfolge ausliefert, wie er sie empfangen hat. Jedes Topic ist ein "Ordered Topic". Da wird nur je ein Topic Upstream und Downstream haben, sind wir hier auf der sicheren Seite. Weitere Verbindungen oder Topics sind für einen Tunnel nicht notwendig. 
			- [ ] So ist aber nur ein Client gleichzeitig möglich. Man könnte überlegen, die Topics dynamisch zu benennen, und so beliebige Clients zuzulassen. Dann muss aber der Server entsprechen diese Topics subscriben. Das kann man optional am Ende untersuchen, wenn das Fundament steht. 
		- Mosquitto unterstützt _ordered message delivery_ standardmäßig, so wie es in der MQTT Spezifikation vorgeschrieben wird.
		- [ ] TODO: QoS 1 oder 2 werden für _order preservation_ empfohlen. Hier können wir noch das QoS in Paho anpassen: `client.publish("topic", "message", qos=1)`. Dabei gilt es dann den Einfluss auf Latenz und Bandbreite zu untersuchen.
		- [ ] TODO: Receive Maximum oder  In-Flight Grenzen entsprechend anpassen
- [ ] **TCP Meltdown** (TCP over TCP):
	- [Numberphile - YouTube](https://www.youtube.com/watch?v=AAssk2N_oPk)
	- MQTT nutzt TCP, tunnelt aber in der Payload nochmals TCP; potentielles Risiko und Performancekiller
	- [Why TCP Over TCP Is A Bad Idea](https://web.archive.org/web/20230228035749/http://sites.inka.de/%7EW1011/devel/tcp-tcp.html)
	- [Avoiding TCP-over-TCP Meltdown in WANs](https://roofman.me/2025/08/20/avoiding-tcp-over-tcp-meltdown-in-wans/)
	- [ ] [What is TCP-over-TCP and how does OpenVPN under TCP mode avoid the issue?](https://serverfault.com/questions/1045786/what-is-tcp-over-tcp-and-how-does-openvpn-under-tcp-mode-avoid-the-issue)
		- By greatly increasing the minimum retransmission timeout of the inner TCP connection, we have effectively disabled the timeout retransmission mechanism of the inner TCP. Therefore, the TCP meltdown problem is avoided. 

	- **Bottomline**:
		- [ ] TODO: Option A: Prüfe und passe bei Bedarf das _minimum retransmission timeout_ der inneren TCP Verbindung signifikant nach oben an. (so macht es OpenVPN im TCP-Mode)
		- [ ] TODO: Option B: Vermeide TCP-over-TCP ganz, indem du im inneren Tunnel kein TCP, sondern UDP verwendest, wie es VPNs wie OpenVPN oder Wireguard eh machen. ([UDP Socket in Python](https://wiki.python.org/moin/UdpCommunication))
- [ ] **Packet Splitting**
	-  TCP Pakete sind kleiner (64 KB) als max. MQTT Message Größe (256 MB), daher keine erneute Aufteilung nötig
	-  Ethernet Frames max. 1500 Bytes (IP Packets theoretisch 64KB über das 16-bit length field, aber praktisch daher auch nur 1500 byte)
	- Daher ist keine eigene Packet Splitting Implementierung notwendig
	- [ ] Dennoch zu testen durch senden größerer Datenmengen
	- [ ] TODO: Durch geschickte MQTT und Socket Konfiguration sollte dies also ausschließbar sein.
		- [ ] **Broker Limits:** `message_size_limit`, `max_queued_bytes`, `max_queued_messages`.
		- [ ] **Inflight Settings:** Wie viele Nachrichten sind unbestätigt unterwegs? Default ist meist 20. Relevant: `max_inflight_bytes`, `max_inflight_messages`.
		- [ ] **Socket:** `_BUFFER_SIZE` anpassen.
		- [ ] **Ziel:** Buffer Size dynamisch an `message_size_limit` des Brokers anpassen.
			- _Problem:_ Kein direktes Abfragen möglich.
			- _Lösungsidee:_ Testweise größere Nachrichten schicken, bis Exception fliegt.
			- **Verworfene Alternativen:** NATS (Performance gut, aber schlechte Firewall-Toleranz), CORBA/AMQP (zu komplex/Enterprise-lastig).
#### Hilfreiche Links zur Implementierung:
- [Mosquitto Manual](https://mosquitto.org/man/mosquitto-8.html)
- [Paho MQTT Documentation](https://pypi.org/project/paho-mqtt/)
#### Andere Protokollkandidaten:
[Welcher IOT Protokoll eignet sich für dein Projekt](https://www.newroom-media.de/blog/mqtt-coap-amqp-welches-iot-protokoll-eignet-sich-fuer-dein-projekt/)
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
___
### Nutzdaten (Passenger)
- [X] TCP Port Forwarding
	- Funktionert, erlaubt SSH, SFTP, ...
	- "_Im Idealfall können Sie dann durch diesen Tunnel z.B. mit SSH, OpenVPN oder Wireguard alles weitere durchtunneln"_. - das ist hiermit erfüllt. SSH läuft hier durch. Innerhalb von SSH kann man dann wiederum beliebig weiter Tunneln.
	- [ ] OpenVPN kann auch auf TCP konfiguriert werden 
		- [ ] Client: `proto tcp-client`, `remote 127.0.0.1 1194`
		- [ ] Server: `proto tcp-server`, `port 1194`
- [ ] UDP
	- [UDP in Python](https://wiki.python.org/moin/UdpCommunication)
	- dynamisches Wechsel zwischen TCP oder UDP je nach Port? 
	- z.B. OpenVPN UDP Port 1194 oder Wireguard Port 51820
- [ ] HTTP
	- Verbindung zu Webserver würde gehen, noch nicht getestet. 
	- Umstellen Target Port 80 oder 443
	- Konfiguration, dass Browser localhost
	- Wirkt nicht so praktisch wie die anderen Lösungen
	- [X] Port Forwarding:
		- `ssh -L 1234:moodle.fernuni-hagen.de:443 mathias@localhost -p 2222` und dann im Browser `localhost:2222`
	- [X] SOCKS Proxy
		- `ssh -D 1234 mathias@localhost -p 2222 -v` und im Browser dann  SOCKS Host localhost mit Port 1234 einstellen
		- Funktioniert, 6 MBit/s Upload, 5 MBit/s Download, Latenz 200 ms. Reicht für einfaches Browsing. Videos ok, Zeitkritsiches wie Livestreaming, Video/Voice Calls nicht 
- [ ] Alternative: IP-Tunnel mittels **TUN Devices** (OpenVPN/Wireguard). Damit gehen TCP, UDP und DNS durch. (Analog zur Einsendeaufgabe 2d)
	- TUN-Device, der sämtlichen Traffic abfängt, statt Socket, der nur auf einem Port lauscht.
	- Bibliotheken `pytun` oder direkt SysCalls mit `fcntl` und `/dev/net/tun` / `os.read(tun_fd, ...)`, ...
	- Analog zur Einsendeaufgabe 2d:
		- [ ] Virtuelle IP Adressen 
			- Subnetz `10.0.0.0/24`
			- Local `10.0.0.2` Remote `10.0.0.1`.
		- [ ] Routing:
			- Routing Tabellen: `ip route add default via 10.0.0.1 dev tun0`
			- Aber eine Host-Route zum zum MQTT muss gesetzt werden, sonst Routing Loop
		- [ ] NAT / Masquerading auf Server Seite.
			- Remote Tunnel muss Paket in eigenes TUN Interface schreiben. 
			- IP Forwarding muss aktiviert sein `sysctl -w net.ipv4.ip_forward=1`
			- NAT Regel: Masquerading, damit er so tut, als käme das Paket vom ihm selbst über `iptables`, sodass die Antwort auch zum Remote zurück kommt, und nicht direkt zum Local
		- [ ] Fragmentierung vermeiden:
			- 1500 Byte Ethernet Frame in TCP verpacken, dadurch ist letzteres größer als 1500 Byte. Das wird dann wiederum fragmentiert. 
			- Daher ggf. MTU vom TUN auf 1400 oder so setzen `sudo ip link set tun0 mtu 1400`

- **Aktueller Test-Status:** Nutzung von SSH als Zwischenschicht (Madrioschka/Frankenstein: `MQTT | SSH | Nutzdaten`), soll aber eliminiert werden zugunsten von reiner `MQTT | Nutzdaten` Implementierung.
	- Hier lassen sich die  Einsendeaufgabe dann ebenfalls drüber tunneln.
		- [x] 2a Port Forwarding 
		- [x] 2b SOCKS Proxy
			- Funktioniert mit ausreichend großer Buffer Size (64KB), sonst Abbrüche SSH: `ssh_dispatch_run_fatal ... message authentication code incorrect`, MQTT: `Broken pipe` / `Connection reset by peer`.  TCP Meltdown?
		- [ ] 2c Remote Tunnel
		- [ ] **2d VPN via TUN**
		- [ ] 2e VPN via TAP
		- [ ] 3 ptunnel
		- [ ] 4 VPN über SSH via ptunnel
___
### Trägerprotokollauswahl (Tunnel/carrier)
[Carrier und Passenger Protokolle](https://tsbates.com/blog/transport-vs-carrier-vs-passenger-protocols/)
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
## Architektur & Design
- [X] Proof of Concept:
	- TCP Socket an bestimmten Port, der dann Packete per MQTT über Broker an anderen Client schickt
	- ermöglicht SSH, SFTP, ...
- [ ] TODO: Zielarchitektur:
	- MQTT Pakete mithilfe der bestehenden Libraries hin und her schicken
	- Dann an TUN Devices weitergeben
- TODO: Multi-Session-Fähigkeit
	- Sollten mehrere Clients gleichzeitig verbinden können?
	- Wenn ja, müsste das entweder über Topics gekapselt werden, oder in den Nutzdaten müsste eine Art Session ID hinterlegt sein, die dann De-serialisiert werden muss beim Empfang.
	- Zu komplex? Solange SOCKS, SSH, und/oder IP via TUN gehen, ist das ausreichend für die Aufgabe.
## Implementierung
- [X] Proof of Concept
	- steht und funktioniert
- [ ] TODO: offene TODO Punkte implementieren
## Test & Validierung
- [ ] TODO: Latenz
- [ ] TODO: Bandbreite
- [ ] TODO: Verbindungsstabilität
- [ ] TODO: ...?
## Dokumentation & Präsentation
- [ ] Präsentation
- [ ] Paper