<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Tibber Reload
## Kurz erklärt
Lädt den Tibber-Config-Eintrag neu, wenn der Spannungssensor länger als 1 Minute unavailable ist.
## Auslöser
1. Status von Spannung L1 (`sensor.voltage_phase1_am_anger_3`) ändert sich auf `unavailable` für 1 Min.

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. festgelegtes Ziel Dienst `homeassistant.reload_config_entry` ausführen

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1750446203882` |
| Modus | `single` |
| Kategorie | Energie & Auto |
| Verwendete Entities | Spannung L1 (`sensor.voltage_phase1_am_anger_3`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
