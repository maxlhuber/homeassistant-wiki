<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Wasser Garten für 1h an
## Kurz erklärt
Schaltet das Garten-Wasserventil per Helfer-Taste für 1 Stunde ein, sofern es aktuell ausgeschaltet ist.
## Auslöser
1. Status von Wasser 1h (`input_button.wasser_1h`) ändert sich

## Bedingungen
- `switch.wasserventil_garten` hat den Status `off`

## Ablauf
1. `switch.wasserventil_garten` einschalten
2. 1 Std. warten
3. `switch.wasserventil_garten` ausschalten

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1750963126863` |
| Modus | `single` |
| Kategorie | Garten & Wasser |
| Verwendete Entities | Wasser 1h (`input_button.wasser_1h`), `switch.wasserventil_garten` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
