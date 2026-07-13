<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Benachrichtigung Fensterkontakt Bad
## Kurz erklärt
Benachrichtigt beide iPhones, wenn das Badfenster 30 Minuten offen steht.
## Auslöser
1. Status von Tür (`binary_sensor.fensterkontakt_bad_contact`) ändert sich auf `on` für 30 Min.

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. Push-Nachricht an Meikes iPhone senden
2. Push-Nachricht an Max' iPhone senden

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768313851346` |
| Modus | `single` |
| Kategorie | Sicherheit & Zugang |
| Verwendete Entities | Tür (`binary_sensor.fensterkontakt_bad_contact`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
