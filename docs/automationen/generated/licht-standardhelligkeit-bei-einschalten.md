<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Licht Standardhelligkeit bei Einschalten
## Kurz erklärt
Setzt bei direkten Light-Turn-On-Befehlen ohne expliziten Helligkeitswert die Standardhelligkeit. Standard ist 100 Prozent, im Flur, Schlafzimmer und Bad sowie deren Hauptlichtern nachts zwischen Sonnenuntergang und Sonnenaufgang 1 Prozent. Explizite Helligkeitsbefehle bleiben unverändert.
## Auslöser
1. Ereignis `call_service` tritt ein
2. Ereignis `call_service` tritt ein

## Bedingungen
- eine interne Vorlagenprüfung ist erfüllt
- eine interne Vorlagenprüfung ist erfüllt

## Ablauf
1. wenn eine interne vorlagenprüfung ist erfüllt, dann eine festgelegte schrittfolge wiederholen
2. wenn eine interne vorlagenprüfung ist erfüllt, dann wenn logische bedingungsgruppe `or` ist erfüllt, dann eine festgelegte schrittfolge wiederholen; andernfalls eine festgelegte schrittfolge wiederholen

## Manuelle Bedienung
Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?

## Technische Angaben
| Feld | Wert |
|---|---|
| Home-Assistant-ID | `1777792801744` |
| Modus | `queued` |
| Kategorie | Licht & Präsenz |
| Verwendete Entities | `light.bad`, `light.diele`, `light.flur`, `light.hue_white_schlafzimmer_decke`, `light.kronleuchter_flur`, `light.lidl_led_panel_bad`, `light.schlafzimmer` |

<p class="page-status">Automatisch erfasst: 12. Juli 2026 · Beschreibung am 13. Juli 2026 live korrigiert</p>
