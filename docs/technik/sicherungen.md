---
search:
  exclude: true
---

# Sicherungen

## Zielzustand

- Regelmäßige Home-Assistant-Sicherungen
- Zusätzliche Kopie außerhalb des Home-Assistant-Thin-Clients
- Wiki-Quelldateien auf dem WD-NAS
- Fertige Offline-Version des Wikis auf dem WD-NAS
- Wiederherstellung mindestens einmal praktisch getestet

## Aktueller Stand

Die automatische Sicherung wird auf dem WD-NAS unter `\\nas.local\backup` gespeichert. Für den Zeitraum vom 8. bis 12. Juli 2026 wurden tägliche Sicherungen jeweils gegen 03:45 Uhr vorgefunden.

| Eigenschaft | Festgestellter Stand |
|---|---|
| Speicherort | WD-NAS, Freigabe `backup` |
| Rhythmus | täglich gegen 03:45 Uhr |
| Verschlüsselung | aktiviert |
| Home-Assistant-Datenbank | enthalten |
| Letzte geprüfte Sicherung | 12. Juli 2026, 03:45 Uhr |

Noch nicht verlässlich dokumentiert sind die Aufbewahrungsregeln, ein zusätzlicher externer Speicherort und ein praktisch getesteter Wiederherstellungsweg. Diese Punkte bleiben deshalb Wartungsaufgaben und werden nicht als vorhandene Absicherung dargestellt.

!!! important "Eine Sicherung ist erst verlässlich, wenn die Wiederherstellung getestet wurde."

<p class="page-status">Zuletzt geprüft: 12. Juli 2026 · Status: Teilweise erfasst</p>
