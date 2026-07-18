---
search:
  exclude: true
---

# Systemübersicht

Diese Seite ist für Wartung. Die Familienansicht erklärt dieselben Systeme vereinfacht unter [So funktioniert unser Smart Home](../grundlagen.md).

## Komponenten

| Komponente | Aufgabe | Netzwerk / Standort | Status am 13. Juli 2026 |
|---|---|---|---|
| Thin Client | Home Assistant OS; eigentliche Smart-Home-Zentrale | Büro, rechte Schublade unter dem Fernseher | In Betrieb; Home Assistant 2026.7.2 |
| Raspberry Pi 4B | Stellt dieses MkDocs-Wiki über Nginx bereit | Büro, rechte Schublade unter dem Fernseher; WLAN; zuletzt `192.168.1.189` | In Betrieb und per SSH erreichbar |
| WD My Cloud EX2 Ultra | Home-Assistant-Sicherungen und Datenspeicher | Büro, rechte Schublade unter dem Fernseher; `nas.local` | In Betrieb |

Die IP-Adresse des Raspberry Pi kann sich ohne feste DHCP-Zuordnung ändern.

## Datenfluss

1. Home Assistant verwaltet Geräte und Automationen auf dem Thin Client.
2. Sicherungen werden auf dem NAS abgelegt.
3. Der Raspberry Pi liest einmal pro Woche ausschließlich freigegebene Dateien aus dem neuesten Backup.
4. Der Pi erzeugt und prüft die Wiki-Seiten, überträgt den Stand nach GitHub und schaltet die neue Website atomar frei.

Der Raspberry Pi greift im normalen Seitenaufruf nicht steuernd auf Home Assistant zu.

<p class="page-status">Laufende Systeme geprüft: 18. Juli 2026</p>
