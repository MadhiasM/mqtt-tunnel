# Dokumentation: Fachpraktikum – MQTT-Tunnel

Projekt: Implementierung eines TCP-Tunnels über ein Message-Broker-Protokoll (MQTT)
Datum: 10.01.2026
Teammitglieder: Robert, Lars, Mathias
## Abstract
- [ ] TODO
## 1. Einleitung und Motivation

In modernen Netzwerkinfrastrukturen stellen Firewalls, NAT-Gateways und Proxies oft Hürden für direkte Verbindungen zwischen Endpunkten dar. Während Standardprotokolle wie HTTP(S) und DNS meist genehmigt sind, werden direkte TCP-Verbindungen für SSH, VPNs oder proprietäre Dienste häufig blockiert.

Ziel dieses Fachpraktikums war die Entwicklung einer Tunnel-Lösung, die ein alternatives Trägerprotokoll nutzt, um Netzwerkbeschränkungen zu umgehen. Gemäß der Aufgabenstellung sollte bewusst auf die "üblichen Verdächtigen" (HTTP/DNS) verzichtet werden. Stattdessen lag der Fokus auf einem Protokoll, das einen Message-Broker verwendet.

Diese Ausarbeitung dokumentiert den Entwurf, die Protokollauswahl, die Implementierung und die Validierung eines Tunnelsystems, das beliebigen TCP-Traffic (am Beispiel von SSH) über das MQTT-Protokoll kapselt und transportiert.
## 2. Analyse und Protokollauswahl
Die zentrale Design-Entscheidung des Projekts war die Wahl des Trägerprotokolls (Carrier Protocol).
### 2.1 Evaluierung der Trägerprotokolle (Carrier)
Für die Wahl des Trägerprotokolls standen verschiedene Broker-basierte Ansätze zur Diskussion. Die zentrale Anforderung war die Wahrscheinlichkeit, strikte Firewalls und NAT-Umgebungen überwinden zu können, sowie die Verfügbarkeit von Bibliotheken für eine zeitgerechte Implementierung.
#### 2.1.1 MQTT (Message Queuing Telemetry Transport)
MQTT ist ein offener, leichtgewichtiger Nachrichten-Standard, der primär für die Machine-to-Machine-Kommunikation (M2M) und das Internet der Dinge (IoT) entwickelt wurde. Es ist darauf optimiert, auch bei unzuverlässigen Netzwerken mit geringer Bandbreite effizient zu arbeiten.
##### Eigenschaften
MQTT basiert auf einem reinen Publish/Subscribe-Prinzip und verzichtet auf komplexe Routing-Mechanismen. Ein zentraler Broker verwaltet die Nachrichtenverteilung. Clients können Nachrichten auf einem Topic (einem hierarchischen String, z. B. `tunnel/upstream`) veröffentlichen (Publish) oder dieses abonnieren (Subscribe). Das Routing erfolgt ausschließlich über diese Topics, die dynamisch zur Laufzeit erstellt werden.
- **Topics & Wildcards:** Ähnlich wie beim AMQP Topic Exchange sind Hierarchien möglich. Clients können mittels Wildcards wie `+` (eine Hierarchieebene) oder `#` (alle folgenden Ebenen) flexible Abonnements steuern.
- **Quality of Service (QoS):** MQTT bietet drei Abstufungen der Zustellgarantie:
    - _QoS 0 (At most once):_ "Fire and Forget". Keine Garantie, minimale Latenz.
    - _QoS 1 (At least once):_ Garantiert die Ankunft, Duplikate sind möglich.
    - _QoS 2 (Exactly once):_ Garantiert die exakte einmalige Ankunft durch einen 4-Wege-Handshake.
- **Session-Features:** Funktionen wie _Last Will & Testament_ (eine Nachricht, die der Broker sendet, wenn der Client die Verbindung unerwartet verliert) und _Retained Messages_ (der Broker speichert den letzten Status für neue Abonnenten) bieten Mechanismen zur Statusüberwachung, die in TCP so nicht direkt enthalten sind.
##### Vorteile
- Der Header einer MQTT-Nachricht ist extrem kompakt (minimal 2 Byte) und hat so einen sehr **geringen Overhead**. Dies ist ideal für einen Tunnel, da das Verhältnis von Nutzdaten zu Protokolldaten sehr günstig ist.
- Neben den Ports 1883/8883 unterstützen fast alle modernen Broker MQTT über WebSockets (Port 443). Da Port 443 (HTTPS) praktisch überall offen ist, eignet sich das Protokoll hervorragend zum **Umgehen von Firewalls**.
- Der Payload ist binär. TCP-Pakete oder auch beliebige andere Daten können also ohne Encoding (wie Base64) direkt in den Body der Nachricht geschrieben werden.
- Sender und Empfänger sind **entkoppelt** und müssen sich nicht kennen oder gleichzeitig online sein (bei Nutzung von Persistent Sessions), was Probleme mit NAT und dynamischen IPs löst.
- Durch die _QoS_ ist es möglich, den **Zielkonflikt** zwischen **Stabilität** und **Bandbreite** gut abzustimmen und durch Tests herauszufinden, in welcher Stufe beide Anforderungen angemessen erfüllt werden können.
- MQTT bietet eine Vielzahl von Bibliotheken und Frameworks in verschiedenen Programmiersprachen, sowohl für den Client als auch den Broker. Diese sind durch die Nutzung sowohl in Industrie als auch im privaten Umfeld "proven in use", also bewährt und müssen nicht mehr selber verifiziert oder qualifiziert werden. Auch reduzieren sie den notwendigen Implementierungsaufwand erheblich, indem sie Abstraktionsebenen bieten und viele Besonderheiten des Protokolls bereits intern umgesetzt sind. Das ermöglicht es, schnell einen Proof-of-Concept beispielsweise in Python auf die Beine zu stellen, um die prinzipielle Eignung des Protokolls für einen Tunnel nachzuweisen und reduziert allgemein die Entwicklungszeit. Sollte es zu Performanceproblemen kommen, ist es später möglich, auf eine performantere Sprache wie C oder Go zu wechseln.
##### Nachteile
- Da MQTT selbst TCP nutzt, um TCP-Pakete zu transportieren ("TCP over TCP"), ist es nicht auszuschließen, dass es bei hohem Paketverlust zu exponentiell steigenden Wartezeiten (Retransmission Timeouts) auf beiden Ebenen kommen. Die nennt man auch **TCP-Meltdown**. 
- Der Broker ist ein **Single Point of Failure** (SPOF). Fällt dieser aus, bricht der Tunnel zusammen. Mit ausreichendem Aufwand ließen sich hier aber Redundanzen implementieren, die ein Hopping zwischen verschiedenen Broker ermöglichen. 
#### 2.1.2 AMQP (Advanced Message Queuing Protocol)
AMQP ist ein binäres Protokoll auf Anwendungsebene, das häufig in Enterprise-Umgebungen (z.B. Bankwesen, Logistik) eingesetzt wird. Es bietet im Vergleich zu MQTT deutlich komplexere Routing-Möglichkeiten und Transaktionssicherheit.
##### Eigenschaften
Der Exchange dient als Verteiler und nimmt alle Nachrichten der Producer, sprich Sender, im Empfang, speichert die Nachrichten aber nicht selber dauerhaft ab. Durch Flow Control kann er den Producern und Consumern (Empfängern) mitteilen, dass eine Queue voll ist und so Überlastung verhindern. Er ist für die Weiterleitung an entsprechende Queues zuständig. Das erfolgt über Bindings, also Regeln für das Routing der Nachrichten über einen Routing Key, der vom Producer in den Nachrichtenheader hinzugefügt wird. 
Dadurch sind flexible Routing-Mechanismen möglich: 
- **Direct Exchange** bietet die Möglichkeit der direkten Adressierung durch einen exakten Match des Routing Keys der Nachricht und Queues, die mit diesem Key verbunden sind. 
- **Fanout Exchange** ähnelt einem Broadcast, der den Routing Key ignoriert und die Nachricht an alle Queues weiterleitet. 
- **Topic Exchange** bietet ein flexibles Routing durch Wörter, die hierarchisch durch Punkte getrennt sind. Auch bietet es Wildcards wie `*` für genau ein Wort oder `#` für eine beliebige Zahl an Wörtern, auch null. Dadurch lässt sich ein komplexes Routing durch den geschickten Einsatz von Hierarchiestufen und Wildcarads realisieren. 
- **Headers Exchange** ignoriert den Routing Key und schaut stattdessen auf den Header, also die Metadaten der Nachricht. Der Header ist standardisiert und erlaubt eine Vielzahl von Attributen. Dort gibt es Key-Value-Paare, wie beispielsweise das Dateiformat oder der Nachrichtentyp. Abhängig von diesen Paaren lässt sich ein Binding definieren, um nur bestimmte Nachrichtentypen an eine Queue weiterzuleiten, unabhängig vom Routing Key. 
##### Vorteile
- Durch die genannten Eigenschaften ist eine **hohe Zuverlässigkeit** und **garantierte Zustellung** durch persistente Queues und Acknowledgement-Systeme und Transaktionen gegeben. 
- Die verschiedenen **Routing-Mechanismen** sind bei gekonntem Einsatz sehr mächtig und bieten maximale Flexibilität. 
- Durch standardisierte Metadaten erlauben **Interoperatbilität** zwischen verschiedenen Systemen und können z.B. über Message-IDs das Routing oder auch das Routing über Headers Exchange zusätzlich verbessern. 
##### Nachteile
- So flexibel und mächtig die Metadaten auch sind, so sehr verursachen sie auch einen Overhead, der die Nutzdatenrate reduziert. Bei einem Tunnel wird so die Bandbreite noch weiter reduziert. 
- Die Mechanismen zur garantierten Zustellung bieten hier keinen signifikanten Vorteil gegenüber den bereits in TCP inkludierten Mechanismen.
- Der Verbindungsaufbau und Handshake ist komplex. Bei instabilen Verbindungen mit häufige, Verbindungswiederaufbau wird die Effizienz so deutlich reduziert.
- Es nutzt die Ports 5672/5671, bei denen nicht gewährleistet ist, dass sie in typischen Einsatzszenarien von Tunneln (Firmennetzwerke, eingeschränkter Internetzugriff in anderen Ländern) freigeschaltet sind. 
#### 2.1.3 CORBA (Common Object Request Broker Architecture)
CORBA ist ein älterer Industriestandard der _Object Management Group_ (OMG), der entwickelt wurde, um Methodenaufrufe zwischen verteilten Objekten über Netzwerk-, Sprach- und Betriebssystemgrenzen hinweg zu ermöglichen.
##### Eigenschaften
Im Zentrum steht der Object Request Broker (ORB), eine Middleware, die als Vermittler zwischen Client- und Server-Objekten agiert. Anders als bei nachrichtenbasierten Protokollen (wie MQTT/AMQP) ruft der Client hier Methoden auf einem entfernten Objekt so auf, als wäre es lokal vorhanden.
- Schnittstellen müssen strikt in einer speziellen Beschreibungssprache definiert werden. Aus dieser Interface Definition Language (IDL) werden sogenannte Stubs (Client-Seite) und Skeletons (Server-Seite) generiert, die das Umwandeln der Daten in ein übertragbares Format übernehmen.
- Das _General Inter-ORB Protocol_  (GIOP) und die Internet-Implementierung (IIOP) regeln die Kommunikation.
- Der ORB verbirgt den Ort, die Implementierungssprache und den Status des Server-Objekts vollständig vor dem Client.
##### Vorteile
- Ermöglicht die Kommunikation zwischen Systemen, die in völlig unterschiedlichen Sprachen geschrieben sind.
- Durch den IDL-Vertrag sind Schnittstellen extrem präzise definiert, was Fehler bei der Datenübergabe minimiert.
##### Nachteile
- Die Einrichtung erfordert das Schreiben von IDL-Dateien, Kompilieren von Stubs/Skeletons und Konfigurieren des ORB. Für einen einfachen Datentunnel ist dieser **Overhead** unverhältnismäßig hoch und bringt unnötige **Komplexität**.
- CORBA nutzt oft **dynamisch ausgehandelte Ports** oder Ports (z. B. IIOP Port 9999 oder 1050), die in fast allen restriktiven Netzwerken blockiert sind. Ein Tunneln über Port 80/443 ist ohne weitere Proxies kaum möglich. Dadurch ist es für einen Tunnel nicht gut geeignet.
- Es gibt kaum moderne, leichtgewichtige Bibliotheken. Das erschwert die schnelle Entwicklung und erfordert so massiven Aufwand, bevor man überhaupt ein funktionierendes Produkt hat.
#### 2.1.4 NATS
NATS ist ein modernes, Cloud-Native Messaging-System. Es fokussiert sich auf maximale Performance, Einfachheit und Skalierbarkeit.
##### Eigenschaften
NATS verwendet ein textbasiertes Protokoll, das sehr einfach zu implementieren und zu debuggen ist. Wie MQTT nutzt es ein Publish/Subscribe-Modell, jedoch mit einem Fokus auf extreme Geschwindigkeit.
- Das Routing ist ähnlich wie Topics bei MQTT, aber ohne persistente Queues im Core-Server. Hier wird es **Subject-Based** genannt.
- Standardmäßig arbeitet NATS nach dem Prinzip **"Fire and Forget"**. Wenn ein Empfänger nicht bereit ist, wird die Nachricht verworfen. Das ermöglicht extremen Durchsatz, da der Server nicht auf Bestätigungen (ACKs) warten muss. Es ähnelt also dem _QoS_ 0 in MQTT
- Eine Erweiterung von NATS, die Persistenz (Speichern von Nachrichten) und garantierte Zustellung ("At least once") hinzufügt, nennt sich **JetStream**. Dies lässt sich mit dem MQTT _QoS_ 1 vergleichen.
- **Auto-Discovery:** NATS-Server können sich automatisch zu einem Cluster oder Mesh verbinden, was die Skalierbarkeit vereinfacht.
##### Vorteile
- **Performance:** NATS bietet extrem niedrige Latenzen und einen sehr hohen Durchsatz, was für einen Tunnel theoretisch ideal wäre.
- **Einfachheit:** Das Protokoll ist simpel gestrickt, es gibt keinen komplexen Handshake wie bei AMQP oder CORBA.
##### Nachteile
- NATS verwendet standardmäßig Port 4222. Dieser Port ist in den meisten Firmen- oder öffentlichen Netzwerken blockiert. Zwar ist WebSocket-Support möglich, aber weniger verbreitet und standardisiert als bei MQTT-Brokern.
- **Zuverlässigkeit vs. Komplexität:** Im Basis-Modus (Core NATS) gibt es keine Zustellgarantie. Paketverluste im Netzwerk würden zu Datenverlust im Tunnel führen. Um dies zu beheben, müsste man _JetStream_ nutzen, was die Komplexität der Implementierung wieder auf ein Niveau hebt, das dem von MQTT oder AMQP entspricht, ohne deren Verbreitungsvorteile bei Firewalls zu bieten.
### 2.2 Entscheidung für MQTT
Nach Auswertung der Vor- und Nachteile der untersuchten Broker-Protokolle fiel die Entscheidung auf **MQTT**. Die Gründe hierfür sind vielfältig:
- MQTT ist eines der am weitesten **verbreiteten** IoT-Protokolle. Es operiert standardmäßig auf Port 1883 (TCP) oder 8883 (TLS). Die Möglichkeit, MQTT über WebSockets (Port 443) zu betreiben, erhöht die **Firewall-Toleranz**. Da Port 443 (HTTPS) in fast allen Netzwerkumgebungen (Firmennetzwerke, öffentliches WLAN) geöffnet ist, bietet MQTT eine exzellente Wahrscheinlichkeit, Firewalls erfolgreich zu passieren.
- Das Publish/Subscribe-Pattern **entkoppelt Sender und Empfänger** vollständig. Der Client (Tunnel-Eingang) und der Server (Tunnel-Ausgang) müssen sich nicht direkt erreichen können; beide müssen lediglich eine ausgehende Verbindung zum Broker aufbauen können. Diese Architektur löst elegant Probleme mit NAT und eingehenden Firewall-Regeln. 
- Für Python, C, Go und Rust existieren **robuste Bibliotheken** (z. B. _Paho MQTT_ als Client und _Mosquitto_ als Broker), die eine **schnelle Umsetzung** des Proof-of-Concept erlaubten, sodass der Fokus auf der Tunnel-Logik liegen kann, ohne dass man Grundlagenarbeit vorab selbst implementiert werden muss. 
- CORBA wurde als veraltete Legacy-Technologie mit zu hoher Komplexität verworfen. AMQP wurde als zu schwergewichtig für einen simplen Tunnel bewertet und bringt einen zu großen Overhead, der für diesen Anwedungsfall eher hinderlich ist. NATS bietet zwar eine sehr geringe Latenz und birgt viele Vorteile, die MQTT auch mitbringt, ist jedoch im Hinblick auf Firewall-Traversal (oft Port 4222) und Standardisierung weniger universell einsetzbar als MQTT.
## 3. Architektur und Design
### 3.1 Konzept: Carrier und Passenger
Wir unterscheiden in unserer Architektur strikt zwischen zwei Ebenen:
1. **Passenger Protocol (Nutzlast/Payload):** Der Traffic, der getunnelt werden soll. In unserer Implementierung ist dies standardmäßig generischer TCP-Traffic (z. B. SSH), kann aber auch als UPD konfiguriert werden.
2. **Carrier Protocol (Träger):** Das Protokoll, das den Transport übernimmt, in dem Fall also MQTT. Falls jedoch andere Carrier ergänzt werden sollen, ist dies durch die Architektur einfach möglich und kann in einem separaten Modul implementiert werden.
Der Tunnel agiert wie folgt: Ein lokaler Socket nimmt TCP-Daten entgegen, verpackt sie als Payload in eine MQTT-Message und publiziert diese auf einem spezifischen Topic. Die Gegenseite abonniert dieses Topic, entpackt die Payload und leitet sie an das eigentliche Ziel weiter. Die Antwort wird dann nach dem selben Prinzip zurückgeleitet.
### 3.2 Komponenten
Das System besteht aus drei Hauptkomponenten:
1. **Local Proxy (Client):** Lauscht auf einem lokalen Port (z. B. 2222). Außerdem baut er die Verbindung zum Broker auf. Bei einer eingehenden Verbindung wird eine Session initiiert.
2. **MQTT Broker:** Der Vermittler (Mosquitto). Er leitet Nachrichten basierend auf Topics weiter (`tunnel/c2s`, `tunnel/s2c`).
3. **Remote Proxy (Server):** Ist mit dem Broker verbunden. Empfängt Datenpakete vom Local Proxy und baut eine TCP-Verbindung zum eigentlichen Ziel (z. B. `localhost:22`) auf.
### 3.3 Implementierungsentscheidungen
- **TCP**-Verbindungen (Sockets) werden direkt getunnelt. Dies ermöglicht die Nutzung von SSH. Dadurch ist eine hohe Flexibilität geboten und innerhalb des SSH-Tunnels können mittels Port-Forwarding (`ssh -L` oder `ssh -D` für SOCKS) beliebige weitere Dienste (HTTP, Mail etc.) oder auch ein VPN mittels TUN/TAP genutzt werden.
- **UDP**-Verbindungen sind ebenfalls möglich und können durch die Carrier-/Passenger-Architektur einfach ausgetauscht und ergänzt werden. Hierüber lassen sich VPN-Dienste wie Wireguard, die üblicherweise auf UDP setzen, einfach integrieren.
- Zur Vereinfachung nutzt der Tunnel **statische Topics** zum Routing: Ein Topic für Upstream-Daten von Cilent zu Server und eines für Downstream-Daten von Server zu Client. Dies ist für einen 1:1 Tunnel ausreichend und kann bei Bedarf ergänzt werden. Bei einer Erweiterung auf eine 1:n Architektur für das parallele Handling mehrerer Clients ist es wichtig, die statischen Topics durch dynamische, zwischen Broker und Client dynamisch vergebene bzw. ausgehandelte Topics zu ersetzen, die nicht einfach durch andere Clients oder Angreifer erraten oder hergeleitet werden können. Dies kann unterstützt werden durch die Konfiguration der Access Control List (ACL), in der definiert werden kann, welche Clients zu welchen Topics subscriben können. 
- Auch bietet das System die Möglichkeit der Authentifizierung über Username und Passwort, (**Authenticity**) und den Zugriff durch Unbefugte zu verhindern. Unterstützt wird das durch die Möglichkeit, über ein CLI-Argument den TLS-Port 8883 zu nutzen, wodurch der Zugriff ohne entsprechende Zertifikate nicht möglich ist und die Vertraulichkeit (**Confidentiality**) sichergestellt ist. Diese Zertifikate müssen vorab zwischen Broker und Client ausgetauscht werden.
- Das **QoS** kann ebenfalls über ein CLI-Argument konfiguriert werden. Eine Anpassung des QoS kann insbesondere bei instabilen Netzwerkbedingungen dazu beitragen, die **Zuverlässigkeit der Datenübertragung** zu erhöhen und somit die Verfügbarkeit (**Availability**) des Systems zu verbessern.
- **Reihenfolge (Ordering):** MQTT garantiert laut Spezifikation (v3.1.1 und v5.0) die Reihenfolge von Nachrichten innerhalb eines Topics bei QoS 0, 1 und 2 (sofern _Max Inflight_ beachtet wird). Wir verlassen uns auf diese Eigenschaft des Brokers, um den TCP-Stream nicht selbst sequenzieren zu müssen.
- **Rollen:** Die Software ist so konzipiert, dass das Skript mittels Kommandozeilenargument (`--role local` oder `--role remote`) in den entsprechenden Modus geschaltet wird. Dies reduziert Code-Duplizierung und vereinfacht die Maintainability.
#### 3.4 Datenintegrität und Sequenzierung
Eine zentrale Frage beim Tunneln von TCP-Streams über einen Message-Broker ist die Erhaltung der Paketreihenfolge. TCP garantiert, dass Daten in der richtigen Reihenfolge bei der Applikation ankommen. Da unser Tunnel diese Daten zerteilt und als einzelne MQTT-Nachrichten versendet, muss sichergestellt sein, dass diese nicht vertauscht werden (z. B. Paket B kommt vor Paket A an).
- Laut MQTT 3.1.1 und 5.0 garantiert der Broker die Reihenfolge (_Ordering_) für Nachrichten innerhalb eines einzelnen Topics und einer einzelnen Verbindung, sofern nur eine Nachricht "in-flight" ist oder QoS-Level genutzt werden, die dies erzwingen.
- Wir verzichten auf einen eigenen Sequenz-Counter (Header) innerhalb der Nutzdaten. Stattdessen verlassen wir uns auf die FIFO-Eigenschaft (First-In-First-Out) des Brokers für ein gegebenes Topic. Mosquitto hält laut Spezifikation die Reihenfolge ein
#### 3.5 Fragmentierung und MTU
Ein weiteres Design-Thema war die Größe der Datenpakete (Maximum Transmission Unit).
- Ethernet-Frames sind meist auf 1500 Byte begrenzt. MQTT-Nachrichten können jedoch bis zu 256 MB groß sein.
- Da wir TCP-Daten aus dem Socket lesen, geschieht dies in Chunks (in unserer Implementierung 4096 Bytes oder dynamisch bis 64 KB). Diese Größe liegt weit unter dem Limit von MQTT. Da MQTT auf TCP aufsetzt, übernimmt der darunterliegende TCP-Stack des Betriebssystems die Fragmentierung der großen MQTT-Nachricht in physikalische Ethernet-Frames. Da TCP ein datenstrom-orientiertes Protokoll ist, kommt es für den Empfänger nicht auf die einzelnen Pakete an, sondern nur auf den Inhalt. Anwendungen (wie SSH) setzen die empfangenen Daten selbstständig wieder zusammen, egal in wie viele kleine Stücke sie unterwegs zerteilt wurden. Solange die Reihenfolge der Daten stimmt, ist die ursprüngliche Paketgröße für die Funktion irrelevant. Eine manuelle Implementierung von _Packet Splitting_ und _Reassembly_ auf Applikationsebene war daher nicht notwendig.
## 4. Implementierung
Die Umsetzung erfolgte in Python unter Verwendung der Bibliothek `paho-mqtt` als Client und `mosquitto` als Broker.
### 4.1 Kernlogik
Der Kern der Anwendung besteht aus zwei asynchronen Vorgängen:
1. Socket-zu-MQTT:
    Ein Thread liest kontinuierlich vom TCP-Socket (`socket.recv()`). Empfangene Bytes werden direkt als Payload via `client.publish()` an den Broker gesendet.
2. MQTT-zu-Socket:
    Über den Callback `on_message` des MQTT-Clients werden eingehende Pakete empfangen und mittels socket.send() in den offenen TCP-Kanal zum Ziel geschrieben.
### 4.2 Herausforderungen & Lösungen
- **TCP Meltdown (TCP-over-TCP):** Das Tunneln von TCP (Passenger) über TCP (MQTT nutzt TCP) ist bekanntermaßen problematisch ("TCP Meltdown"). Paketverluste auf der Trägerschicht führen zu Retransmissions, während die innere Schicht ebenfalls in Timeouts läuft, was die Verbindung extrem verlangsamen kann.
    - _Lösung:_ Wir haben die Buffer-Sizes der Sockets erhöht (bis zu 64KB), um den Durchsatz zu stabilisieren. Für den produktiven Einsatz wäre ein Wechsel auf UDP im Carrier (z. B. MQTT-SN) oder IP-Tunneling via TUN-Interface denkbar, was in unseren Tests als "Next Step" identifiziert wurde.
- **Verbindungsabbau:** Ein kritischer Punkt war das saubere Schließen von Verbindungen. Wenn der SSH-Client die Verbindung beendet, muss dies über MQTT signalisiert werden, damit auch der Remote Proxy die Verbindung zum Ziel-Server kappt. Aktuell wird dies über Exception-Handling beim Lesen des Sockets realisiert.
- **Puffer & Fragmentierung:** Da TCP ein Stream-Protokoll ist und keine Paketgrenzen kennt, MQTT aber nachrichtenbasiert arbeitet, liest unsere Implementierung Chunks (z.B. 4096 Bytes). Wir haben festgestellt, dass MQTT-Payloads bis 256 MB groß sein können, sodass keine eigene Fragmentierung notwendig war, da Ethernet-Frames (MTU 1500) deutlich kleiner sind.

- [ ] TODO:
-  [ ] TCP: 
	- SSH
	- SOCKS
	- TUN
-  [ ] UDP:
	- Wireguard

## 5. Testen und Validierung
Der Tunnel wurde in verschiedenen Szenarien getestet. Zum Einsatz kamen `tcpdump` und `Wireshark` zur Analyse des Netzverkehrs sowie Standard-Clients (OpenSSH) für Funktionstests.
### 5.1 Funktionstests
- **SSH Login:** Erfolgreich. Ein Login via `ssh -p 2222 user@localhost` (wobei localhost der Tunnel-Eingang ist) auf den Remote-Server war möglich.
- **SOCKS Proxy:** Erfolgreich. Durch Nutzung von `ssh -D` durch den MQTT-Tunnel konnte ein Webbrowser betrieben werden.
    - _Ergebnis:_ Webseitenaufbau funktioniert. Video-Streaming (YouTube) ist möglich, jedoch mit Pufferzeiten.
- **HTTP:** Erfolgreich. HTTP-Requests konnten durch Port-Forwarding transportiert werden.
- **TUN/TAP**:
	-  [ ] TODO
- **Wireguard** via UDP: 
	-  [ ] TODO
-  [ ] TODO: Traces, Screenshots, ...
### 5.2 Wireshark Analyse
Ein Mitschneiden des Traffics zeigte, dass von außen für Dritte nur eine TCP-Verbindung zum MQTT-Broker (Port 1883) sichtbar ist. Der Inhalt der Pakete ist binär (MQTT Payload).
- Sicherheit: Ohne TLS (Port 1883) ist die Payload theoretisch lesbar. Da wir jedoch SSH tunneln, sind die Nutzdaten durch SSH selbst verschlüsselt. Ein Dritter sieht nur verschlüsselte SSH-Pakete innerhalb von MQTT-Publish-Messages. Bei Nutzung von Port 8883 (MQTTS) wäre auch der Metadaten-Verkehr verschlüsselt.
- [ ] TODO: Ergänzen, ...
### 5.3 Performance und Probleme
- **Latenz:** Die Latenz ist durch den "Hop" über den Broker spürbar erhöht (ca. 100 ms Round-Trip-Time (RTT) beim Speedtest im SOCKS-Test).
	- [ ] TODO: Screenshots/Daten von a) direkter Netzwerkverbindung b) SOCKS Proxy c) SOCKS-Proxy über MQTT
- **Stabilität:** Bei sehr großen Datenmengen oder schlechter Verbindung kam es zu `Broken Pipe` Fehlern. Durch Anpassung der `Quality of Service` (QoS) und der Socket-Buffer konnte dies verbessert werden.
- **UDP:** Ein Versuch, UDP-Traffic zu tunneln, wurde unternommen, war jedoch im aktuellen Implementierungsstand nicht stabil. Der Fokus verblieb daher auf TCP.
	- [ ] TODO: Updaten
## 6. Projektmanagement & Arbeitsverteilung
Die Aufgaben wurden im Team wie folgt verteilt:
- **Mathias:**
    - Erstellung eines Proof-of-Concepts des Tunnels unter Nutzung von Paho, Mosquitto und Sockets in Python, Testing mit einem Jetson Nano als Broker / Server und einem Laptop als Client, jeweils in Linux
    - Refactoring in Carrier/Passenger-Architektur für Erweiterbarkeit, Decoupling und Separation of Concerns
    - [ ] Logging 
    - Dokumentation des Fortschritts und der Arbeitspakete in einem Markdown-Dokument
- **Robert:**
    - Bereitstellung der Infrastruktur über vServer (MQTT Broker Server, VPN Server).
    - Durchführung der Latenzanalyse und Wireshark-Untersuchungen.
    - Optimierung der Socket-Robustheit.
    - Umsetzung eines UDP-Passengers als Erweiterung zur TCP-Implementierung
- **Lars:** 
    - Untersuchung der MQTT QoS-Level (0, 1, 2) und deren Einfluss auf den Durchsatz (`max_inflight`).
    - Tests mit UDP.
    - Tests eines VPNs über TUN
    - Tests mit iperf2/3
    - Tests mit Windows
- [ ] TODO: 
	- Dokumentation, Paper-/Präsentations-Erstellung.
## 7. Fazit und Ausblick
Das Projekt zeigt erfolgreich, dass MQTT als Trägerprotokoll für einen TCP-Tunnel geeignet ist. Die Implementierung erfüllt die Anforderung, Netzwerkrestriktionen zu umgehen, indem sie Standard-TCP-Verbindungen in MQTT-Nachrichten kapselt.
Zwar ist die Performance durch den TCP-over-TCP Overhead und das Routing über den Broker limitiert, für administrative Aufgaben (SSH-Shell) oder einfaches Web-Browsing ist die Lösung jedoch praktikabel.
Nächste Schritte (Ausblick):
Für das Deployment bzw. einen offiziellen Release wäre der nächste logische Schritt die Implementierung eines echten IP-Tunnels mittels TUN-Devices ohne SSH als Middlelayer. Dies würde erlauben, nicht nur TCP, sondern auch UDP und ICMP transparent zu übertragen und würde die Applikation als vollwertiges VPN positionieren. Zudem sollte die Unterstützung für MQTT über WebSockets (Port 443) final integriert werden, um maximale Firewall-Transparenz zu gewährleisten.
Aktuell lässt der Tunnel nur eine 1:1 Verbindung zu. Um die Skalierbarkeit zu erhöhen, wäre es hier sinnvoll, das Handling von meheren Clients zu ermöglichen. Hierfür wäre ein Control Channel notwendig, der das Aushandeln von Kommunikationsparametern (z.B. dem Upstream- und Downstream-Topic zwischen einem Client und dem Server) zulässt. Die eigentliche Kommunikation kann dann über das Client-spezifische Topic erfolgen, das eine Session-ID enthält und somit für andere Clients nicht sichtbar ist. Wichtig ist es, dass hier sichergestellt ist, dass ein andere Client oder ein Angreifer nicht die Möglichkeit hat, durch Erraten der Session-ID den gesamten Traffic eines anderen Clients abzufangen. 
# TODO:
- Code Cluenup: Issues (logging, udp, cli-arguments, config.json, ACL...). Finale Version muss funktionieren
- Paper als PDF, Code als `.tar.gz`
- Folien für Vortrag aus Paper ableiten
- Prüfung Abschnitte 3.4 und 3.5 - so korrekt?
- Wieso kein allgemeiner IP-Tunnel?
- Grafiken / Diagramme zur Erklärung der Architektur (Client - Broker - Server)
- WebSockets Port 443?
- Quellen?
- Kurze Erklärung (Einrichten/Starten Broker, Starten Clients mit passenden CLI-Arguments)
- Retransmission Timeout (RTO) und Exponential Backoff - Retry (TCP) in Test / Analyse von iperf
- Performance Limitierung: Wie viele Messages kann der MQTT Broker pro Sekunde verarbeiten: Möglicher Bottleneck vServer (schwache Hardware)
	- Testing mit höherperformantem Server als Broker notwendig, sprengt den Rahmen dieses Projekt: Ausblick
- Markdown ausreichend? Oder besser latex?
- README in github anpassen - Usage instruction
- Screenshots Testergebnisse
- Topic {topic}/upstream - {topic}/downstream
- TCP / UDP über Kommandozeile
- TLS 8883 Traces
