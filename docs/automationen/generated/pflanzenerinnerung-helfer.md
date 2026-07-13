<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Pflanzenerinnerung Helfer
## Kurz erklärt
Beendet die Pflanzenerinnerung, wenn die Mobile-App-Aktion "gegossen" ausgelöst wird.
## Auslöser
1. Ereignis `mobile_app_notification_action` tritt ein

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. Gießkanne (`input_boolean.giesskanne`) ausschalten

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1680326169555` |
| Modus | `single` |
| Kategorie | Garten & Wasser |
| Verwendete Entities | Gießkanne (`input_boolean.giesskanne`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
