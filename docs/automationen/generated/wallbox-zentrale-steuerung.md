<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Wallbox Zentrale Steuerung
## Kurz erklärt
Steuert die Wallbox abhängig vom Zielstatus: Sicherheitsladen und preisoptimiertes Laden erzwingen das Laden; Warten und Voll geladen stoppen das Laden. Reagiert auf Statuswechsel und auf das Anstecken des Autos.
## Auslöser
1. Status von Wallbox Zielstatus (`sensor.wallbox_zielstatus`) ändert sich
2. Status von Car connected (`binary_sensor.go_echarger_252938_car`) ändert sich auf `on`

## Bedingungen
- Car connected (`binary_sensor.go_echarger_252938_car`) hat den Status `on`

## Ablauf
1. zwischen 2 Ablaufvarianten wählen

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `wallbox_central_control` |
| Modus | `restart` |
| Kategorie | Energie & Auto |
| Verwendete Entities | Car connected (`binary_sensor.go_echarger_252938_car`), Force state dont charge (`button.go_echarger_252938_frc_2`), Force state charge (`button.go_echarger_252938_frc_3`), Wallbox Zielstatus (`sensor.wallbox_zielstatus`) |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>
