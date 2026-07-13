<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Tür öffnen wenn Max zuhause ankommt
## Kurz erklärt
Öffnet den Nuki Öffner, wenn Max oder Meike nach 30 Sekunden wieder zuhause sind.
## Auslöser
1. Status von Hase (`device_tracker.max_iphone`), Meikes iPhone (`device_tracker.meikes_iphone`) ändert sich von `not_home` auf `home` für 30 Sek.

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. Nuki Öffner Lock (`lock.nuki_offner_lock`) öffnen

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768477812326` |
| Modus | `single` |
| Kategorie | Sicherheit & Zugang |
| Verwendete Entities | Hase (`device_tracker.max_iphone`), Meikes iPhone (`device_tracker.meikes_iphone`), Nuki Öffner Lock (`lock.nuki_offner_lock`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
