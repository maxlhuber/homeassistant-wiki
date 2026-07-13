<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Wasserventil nach 2h aus
## Kurz erklärt
Schaltet das Garten-Wasserventil 2 Stunden nach dem Einschalten automatisch wieder aus.
## Auslöser
1. Status von `switch.wasserventil_garten` ändert sich auf `on`

## Bedingungen
Keine zusätzlichen Bedingungen in der Automation hinterlegt.

## Ablauf
1. 2 Std. warten
2. `switch.wasserventil_garten` ausschalten

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1744732182203` |
| Modus | `single` |
| Kategorie | Garten & Wasser |
| Verwendete Entities | `switch.wasserventil_garten` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
