---
search:
  exclude: true
---

# Offene Prüfpunkte

Diese Punkte sind bei der automatischen Bestandsaufnahme aufgefallen. Sie sind nicht automatisch Fehler, sollten aber bewusst bestätigt oder angepasst werden.

## Am 13. Juli 2026 erledigt

- Der Rauchmelder im Büro benachrichtigt jetzt **Max und Meike**. Beide Versandwege laufen unabhängig voneinander weiter, falls ein Telefon vorübergehend nicht erreichbar ist.
- Die Spülmaschinen-Fertigmeldung geht jetzt ebenfalls an **Max und Meike**.
- Die Beschreibung des Flurlichts nennt nun korrekt, dass außerhalb von 08:00 bis 18:00 Uhr derzeit keine Aktion erfolgt.
- Die Beschreibung der Standardhelligkeit nennt nachts korrekt **1 %** statt 10 %.
- Die Wallbox-Ladebenachrichtigung zeigt den Preis korrekt in **ct/kWh** an.
- Aus der Szene **„Filmabend“** wurden der nicht mehr vorhandene Osram-Stripe und der bewusst deaktivierte „Do not disturb“-Schalter entfernt. Die Szene enthält jetzt drei aktive Licht-Entities.
- Die zusätzlichen täglichen und wöchentlichen Recorder-Bereinigungsautomationen sind ausgeschaltet. Der Recorder verwaltet die Aufbewahrung bereits selbst.
- **„Wallbox Override Reset“** bleibt ausgeschaltet, da `switch.wallbox_override` nicht mehr vorhanden ist.

## Sicherheitsrelevant

### Automatische Türöffnung bei Ankunft

Die Automation **„Tür öffnen wenn Max zuhause ankommt“** öffnet den Nuki-Öffner, wenn Max oder Meike von `not_home` auf `home` wechseln und dieser Zustand 30 Sekunden besteht. Es sind keine weiteren Bedingungen in der Automation hinterlegt.

Zu prüfen: Soll die Tür wirklich bei jeder erkannten Rückkehr automatisch geöffnet werden, und gibt es außerhalb dieser Automation noch Schutzmechanismen?

[Automation ansehen](../automationen/generated/tuer-oeffnen-wenn-max-zuhause-ankommt.md)

## Organisation

- Die Etage **„Ergeschoss“** ist in Home Assistant vermutlich falsch geschrieben. Das Wiki zeigt „Erdgeschoss“ an, verändert Home Assistant aber nicht.
- **126 von 266 Geräten** sind keinem Raum zugeordnet. Ein großer Teil davon sind virtuelle Dienste oder Bedienkarten; physische Geräte sollten schrittweise geprüft werden.
- Die beiden Szenen heißen **„test“** und **„Filmabend“**. Die Testszene sollte auf ihren aktuellen Zweck geprüft werden; „Filmabend“ wurde bereinigt.

<p class="page-status">Bestandsaufnahme vom 12. Juli 2026 · Sichere Korrekturen am 13. Juli 2026 live geprüft</p>
