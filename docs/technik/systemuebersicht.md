---
search:
  exclude: true
---

# Systemübersicht

Diese Seite ist für Wartung. Die Familienansicht erklärt dieselben Systeme vereinfacht unter [So funktioniert unser Smart Home](../grundlagen.md).

## Komponenten

| Komponente | Aufgabe | Netzwerk / Standort | Status am 13. Juli 2026 |
|---|---|---|---|
| Thin Client | Home Assistant OS; eigentliche Smart-Home-Zentrale | Physischer Standort noch nicht dokumentiert | In Betrieb; Home Assistant 2026.7.1 |
| Raspberry Pi 4B | Stellt dieses MkDocs-Wiki über Nginx bereit | WLAN; zuletzt `192.168.1.189` | In Betrieb und per SSH erreichbar |
| WD My Cloud EX2 Ultra | Home-Assistant-Sicherungen und Datenspeicher | `nas.local`; physischer Standort noch nicht dokumentiert | In Betrieb |

Die IP-Adresse des Raspberry Pi kann sich ohne feste DHCP-Zuordnung ändern. Der physische Standort von Thin Client, NAS, Router und Raspberry Pi muss bei einem Rundgang ergänzt werden.

## Datenfluss

1. Home Assistant verwaltet Geräte und Automationen auf dem Thin Client.
2. Sicherungen werden auf dem NAS abgelegt.
3. Ein lokaler Export erzeugt die Wiki-Seiten.
4. Das fertige Wiki wird auf den Raspberry Pi übertragen.

Der Raspberry Pi greift im normalen Seitenaufruf nicht steuernd auf Home Assistant zu.

<p class="page-status">Laufende Systeme geprüft: 13. Juli 2026</p>
