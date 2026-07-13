# So funktioniert unser Smart Home

Ein Smart Home besteht hier nicht aus einem einzigen Gerät. Sensoren und Schalter melden etwas an Home Assistant; Home Assistant entscheidet anhand einer Automation, ob es eine Aktion ausführt.

> **Sensor oder Taster → Home Assistant → Automation → Licht, Gerät oder Nachricht**

Beispiel: Der Türkontakt meldet „Speisekammertür offen“. Home Assistant schaltet das Licht ein. Beim Schließen meldet der Kontakt „Tür zu“ und Home Assistant schaltet das Licht wieder aus.

## Die beteiligten Systeme

### Home-Assistant-Thin-Client

Auf dem Thin Client läuft **Home Assistant OS**. Das ist die Zentrale: Dort liegen Geräte, Räume, Automationen und das Dashboard. Wenn der Thin Client nicht läuft, kann das Wiki trotzdem erreichbar sein, aber die Smart-Home-Steuerung ist gestört.

### Raspberry Pi

Der Raspberry Pi stellt **nur dieses Wiki** im Heimnetz bereit. Änderungen am Wiki schalten keine Lampe und öffnen keine Tür. Umgekehrt bedeutet ein erreichbares Wiki nicht automatisch, dass Home Assistant funktioniert.

### WD My Cloud EX2 Ultra

Das NAS bewahrt Home-Assistant-Sicherungen auf. Es ist für Wiederherstellung und Wartung wichtig, steuert aber im Normalbetrieb keine Lampe.

## Fünf Begriffe ohne Technikdeutsch

| Begriff | Bedeutung | Beispiel |
|---|---|---|
| Gerät | Ein physischer Gegenstand im Haus | Wandschalter, Rauchmelder, Lampe |
| Sensor | Misst oder erkennt etwas | Temperatur, offene Tür, Anwesenheit |
| Automation | Eine Wenn-dann-Regel | Wenn die Tür aufgeht, Licht einschalten |
| Szene | Gespeicherte gemeinsame Einstellung mehrerer Geräte | Filmabend |
| Home-Assistant-App | Bedienoberfläche und Quelle einiger Handy-Meldungen | Licht bedienen, Standort „zu Hause“ melden |

## Was funktioniert ohne Internet?

Viele lokale Schalter, Funkgeräte wie Sensoren und Lampen (bei uns häufig über den Funkstandard **Zigbee**) sowie Automationen können im Heimnetz weiterarbeiten. Cloud-Dienste, Sprachassistenten, Daten von Internetdiensten sowie Meldungen oder Bedienung von unterwegs können ausfallen. Ob eine einzelne Funktion weiterläuft, hängt von den beteiligten Geräten ab.

## Zugriff von unterwegs

Dieses Raspberry-Pi-Wiki ist derzeit nur im Heimnetz nachweislich erreichbar. Es darf nicht durch eine einfache Router-Portfreigabe ungeschützt ins Internet gestellt werden. Für einen späteren Zugriff von unterwegs ist ein abgesicherter VPN-Zugang die passende Lösung; dieser ist im aktuellen Stand noch nicht eingerichtet.

## Was bedeutet der Standort im Wiki?

- **In Home Assistant bestätigt:** Raum und Etage sind dort direkt hinterlegt.
- **Aus Name/Funktion abgeleitet:** Die Zuordnung ist sehr wahrscheinlich, aber in Home Assistant noch nicht gepflegt.
- **Noch offen oder mobil:** Es wurde bewusst kein fester Raum erfunden.

Eine genaue Position wie „an der Decke“ erscheint nur, wenn sie sicher aus dem Gerätenamen folgt. Weitere Positionen können nach einem Rundgang ergänzt werden.

## Wenn etwas merkwürdig reagiert

1. Prüfen, ob nur ein Gerät oder mehrere Bereiche betroffen sind.
2. Den normalen Schalter beziehungsweise die direkte Bedienung versuchen.
3. Nichts löschen, neu koppeln oder zurücksetzen.
4. Uhrzeit, Raum und Beobachtung notieren.
5. In der passenden [Raumseite](raeume/index.md), [Automationsseite](automationen/index.md) oder [Schnellhilfe](schnellhilfe/index.md) nachsehen.

<p class="page-status">Mit dem laufenden System abgeglichen: 13. Juli 2026</p>
