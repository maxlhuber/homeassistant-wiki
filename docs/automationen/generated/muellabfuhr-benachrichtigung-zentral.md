<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Müllabfuhr Benachrichtigung Zentral
## Kurz erklärt
Sammelt alle Müllarten, die am nächsten Tag abgeholt werden, und verschickt um 18:00 eine Erinnerung zum Rausstellen der Tonnen.
## Auslöser
1. Zeitpunkt `18:00:00` ist erreicht

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. einen internen Verarbeitungsschritt ausführen
2. wenn eine interne vorlagenprüfung ist erfüllt, dann push-nachricht an meikes iphone senden

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1776706598749` |
| Modus | `single` |
| Kategorie | Haushalt |
| Verwendete Entities | AbfallBio (`sensor.abfallbio`), AbfallPapier (`sensor.abfallpapier`), AbfallRecycling (`sensor.abfallrecycling`), AbfallRestmuell (`sensor.abfallrestmuell`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
