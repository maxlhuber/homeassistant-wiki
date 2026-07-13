<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Wasser Garten für 30min an
## Kurz erklärt
Schaltet das Garten-Wasserventil per Helfer-Taste für 30 Minuten ein, sofern es aktuell ausgeschaltet ist.
## Auslöser
1. Status von Wasser 30 min (`input_button.wasser_30_min`) ändert sich

## Bedingungen
- `switch.wasserventil_garten` hat den Status `off`

## Ablauf
1. `switch.wasserventil_garten` einschalten
2. 30 Min. warten
3. `switch.wasserventil_garten` ausschalten

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1750963309351` |
| Modus | `single` |
| Kategorie | Garten & Wasser |
| Verwendete Entities | Wasser 30 min (`input_button.wasser_30_min`), `switch.wasserventil_garten` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
