---
search:
  exclude: true
---

<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Wallbox Override Reset

!!! info "Status: ausgeschaltet"
    Die früher verwendete Wallbox-Override-Funktion existiert nicht mehr. Diese Automation bleibt deshalb ausgeschaltet.

**Ort:** kein fester Raum – betrifft das ganze Haus

## Das bemerkst du im Alltag

Setzt den Wallbox\-Override nach 2 Stunden wieder aus und informiert Max per Push\-Nachricht.

## Sie startet, wenn …

1. Switch.wallbox override wechselt auf „eingeschaltet“ und bleibt dort 2 Std.

## Sie läuft nur weiter, wenn …

Keine weitere Voraussetzung ist hinterlegt.

## Dann passiert …

1. Switch.wallbox override ausschalten
2. Push-Nachricht an Max' iPhone senden

## So kannst du reagieren

Nicht verwenden. Die Seite bleibt nur als Wartungshinweis erhalten.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Wallbox Override Reset |
    | Home-Assistant-ID | 1742245735922 |
    | Modus | single |
    | Kategorie | Energie & Auto |

</div>

<p class="page-status">Definition aus Backup vom 16. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
