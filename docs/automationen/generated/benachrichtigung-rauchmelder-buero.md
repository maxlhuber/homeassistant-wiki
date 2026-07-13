<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Benachrichtigung Rauchmelder Büro
## Kurz erklärt
Sendet Max und Meike eine Alarmmeldung, wenn der Rauchmelder im Büro Rauch erkennt.
## Auslöser
1. Geräteereignis „smoke“ von Rauch (`binary_sensor.rauchmelder_buro_smoke`)

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. Push-Nachricht an Max' iPhone senden
2. Push-Nachricht an Meikes iPhone senden

Beide Nachrichten sind voneinander entkoppelt: Ist ein Telefon nicht erreichbar, wird der Versand an das andere trotzdem versucht.

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1768313703595` |
| Modus | `single` |
| Kategorie | Sicherheit & Zugang |
| Verwendete Entities | Rauch (`binary_sensor.rauchmelder_buro_smoke`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Empfänger am 13. Juli 2026 live aktualisiert</p>
