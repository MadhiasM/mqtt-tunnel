# mqtt-tunnel

Team: Robert, Lars, Mathias

## Planung
### Analyse
#### Organisation
- [ ] Rollenverteilung: Leitung, Architektur, Implementierung, Testing
- [X] Kommunikationskanal: [Discord](https://discord.com/channels/@me/1424823853447905312)
- [ ] VCS + Hosting: [GitHub](https://github.com/MadhiasM/mqtt-tunnel)
#### Anforderungen
- siehe [Moodle](https://moodle.fernuni-hagen.de/course/section.php?id=35887)

- Tunnel sollte Protokoll verwenden, das trotz Firewalling / Proxies verfügbar ist

1. [ ] Erörtern Sie, welches Protokoll Ihr Trägerprotokoll wird.
	- Broker-Basiertes Protokoll, wo es bisher noch nicht so viele Lösungen gibt:
		- [ ] Warum MQTT?
		- [ ] Zuhilfenahme von Tools/Frameworks explizit empfohlen
2. [ ] Erörtern Sie, ob Sie allgemein alle TCP oder UDP oder IP-Verbindungen tunneln wollen, oder nur HTTP(S).
	- [ ] Welche Protokolle werden getunnelt?
		- [ ] Idealfall: alles weitere mittels SSH, OpenVPN oder Wireguard durchtunneln
		- [ ] Alternativ: Nur HTTP(s) Anfragen tunneln
		- [ ] Muss begründet werden
3. [ ] Implementieren Sie Ihren Tunnel. Dokumentieren Sie Implementationsentscheidungen.
	- Hinweis: Dazu sollten Sie auch die Anforderungen und Lösungsideen gründlich analysieren, der Anspruch ist, daß die Beschreibung zwar abstrakt, aber konkret genug ist, daß auf Ihr Darstellung aufbauend jemand die Implementierung erfolgreich starten kann. Der Teufel liegt bekanntlich im Detail, das vielleicht auch erst bei Tests und der Umsetzung auffällt, das müssen Sie nicht entdecken. Die Ergebnisse sollten sich in Ihrem Paper wiederfinden.	
	
4. Testen Sie Ihren Tunnel gründlich. Dazu gehört auch, den Tunnel mal mit tcpdump, Wireshark o.ä. aufzuzeichnen und zu prüfen, was ein Dritter sieht. 

5. Dokumentieren Sie in Ihrer Abgabe, welche Gruppenmitglieder an welchem Teil der Aufgabe mitgewirkt haben, wer für welchen Teil "den Hut auf hatte" und welchen Anteil welches Gruppenmitglied an dem Teil hatte. Im Idealfall sollten im Ergebnis alle Gruppenmitglieder etwa gleich viel geleistet haben.

#### Trägerprotokollauswahl (Tunnel) (carrier)
[Carrier und Passanger Protokolle](https://tsbates.com/blog/transport-vs-carrier-vs-passenger-protocols/)


#### Nutzprotokollauswahl (getunnelt) (passenger)


### Architektur & Design

### Implementierung

### Test & Validierung

### Dokumentation
