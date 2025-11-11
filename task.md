Es gibt verschiedene Wege und Protokolle, über die sich ein Tunnel realisieren lässt. Allerdings ist es empfehlenswert, einen Tunnel über ein Protokoll zu wählen, das mit einer hohen Wahrscheinlichkeit in einem Netzwerk trotz Firewalling und vielleicht sogar irgendwelcher Proxies verfügbar ist. Das schränkt die Auswahl schon etwas ein.

Vielversprechend und entsprechend häufig genutzt sind
- HTTP / HTTPS
- DNS

Die wollen wir in diesem Praktikum daher nicht nutzen, das wäre ja langweilig - stattdessen wollen wir einen "Exoten" nutzen: Ein Protokoll, dass einen Message-Broker nutzt, wie 
- MQTT
- CORBA

In Ihrer Gruppe wählen Sie eines dieser Protokolle oder ein weiteres broker-basiertes Protokoll aus, dokumentieren das "Warum" (es gibt kein "richtig" und "falsch", aber Ihre Beweggründe sind interessant) und entwickeln, möglichst unter Zuhilfenahme vorhandener Tools / Frameworks / bekannter Lösungen eine Implementierung, um einen Tunnel zu ermöglichen.
Im Idealfall können Sie dann durch diesen Tunnel z.B. mit SSH, OpenVPN oder Wireguard alles weitere durchtunneln, alternativ beschränken Sie sich darauf, daß Ihr Tunnel HTTP(S)-Anfragen durchleitet. Was Sie anbieten, ist eine Design-Entscheidung. Auch dafür sollten Sie die Argumente wieder dokumentieren. Auch hier geht es um die Überlegungen, nicht um ein "richtig" oder "falsch".
Ihre Aufgaben für die Gruppenarbeit sind also:
- [ ] Erörtern Sie, welches Protokoll Ihr Trägerprotokoll wird.
- [ ] Erörtern Sie, ob Sie allgemein alle TCP oder UDP oder IP-Verbindungen tunneln wollen, oder nur HTTP(S).
- [ ] Implementieren Sie Ihren Tunnel. Dokumentieren Sie Implementationsentscheidungen.
- [ ] Hinweis: Dazu sollten Sie auch die Anforderungen und Lösungsideen gründlich analysieren, der Anspruch ist, daß die Beschreibung zwar abstrakt, aber konkret genug ist, daß auf Ihr Darstellung aufbauend jemand die Implementierung erfolgreich starten kann. Der Teufel liegt bekanntlich im Detail, das vielleicht auch erst bei Tests und der Umsetzung auffällt, das müssen Sie nicht entdecken.
- [ ] Die Ergebnisse sollten sich in Ihrem Paper wiederfinden.
- [ ] Testen Sie Ihren Tunnel gründlich. Dazu gehört auch, den Tunnel mal mit tcpdump, Wireshark o.ä. aufzuzeichnen und zu prüfen, was ein Dritter sieht.
- [ ] Dokumentieren Sie in Ihrer Abgabe, welche Gruppenmitglieder an welchem Teil der Aufgabe mitgewirkt haben, wer für welchen Teil "den Hut auf hatte" und welchen Anteil welches Gruppenmitglied an dem Teil hatte. Im Idealfall sollten im Ergebnis alle Gruppenmitglieder etwa gleich viel geleistet haben.
