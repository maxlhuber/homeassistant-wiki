<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Wallbox Zentrale Steuerung

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Garage · Außenbereich

## Das bemerkst du im Alltag

Steuert die Wallbox abhängig vom Zielstatus: Sicherheitsladen und preisoptimiertes Laden erzwingen das Laden; Warten und Voll geladen stoppen das Laden. Reagiert auf Statuswechsel und auf das Anstecken des Autos.

## Sie startet, wenn …

1. Der gewünschte Ladezustand ändert sich oder das Auto wird angesteckt.

## Sie läuft nur weiter, wenn …

- Das Auto ist an der Wallbox angeschlossen.

## Dann passiert …

1. Bei „Sicherheitsladen“ oder „preisoptimiert laden“ gibt Home Assistant das Laden frei.
2. Bei „Warten“ oder „voll geladen“ stoppt Home Assistant die Ladefreigabe.

## So kannst du reagieren

Ladezustand und Freigabe zusätzlich am Fahrzeug beziehungsweise an der Wallbox kontrollieren.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Wallbox Zentrale Steuerung |
    | Home-Assistant-ID | wallbox\_central\_control |
    | Modus | restart |
    | Kategorie | Energie & Auto |
    | Verwendete Entities | Car connected (`binary_sensor.go_echarger_252938_car`), Force state dont charge (`button.go_echarger_252938_frc_2`), Force state charge (`button.go_echarger_252938_frc_3`), Wallbox Zielstatus (`sensor.wallbox_zielstatus`) |

</div>

<p class="page-status">Definition aus Backup vom 16. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
