<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Automatische Standardhelligkeit

!!! success "Status: aktiv"
    Diese Automation ist in Home Assistant eingeschaltet.

**Ort:** Bad · Erdgeschoss, Flur · Erdgeschoss, Schlafzimmer · Erdgeschoss

## Das bemerkst du im Alltag

Setzt bei einem Einschaltbefehl ohne gewählte Helligkeit normalerweise 100 %. Im Flur, Schlafzimmer und Bad werden die Hauptlichter nachts auf 1 % gesetzt. Eine ausdrücklich gewählte Helligkeit wird nicht verändert.

## Sie startet, wenn …

1. Ein unterstütztes Licht erhält einen Einschaltbefehl.

## Sie läuft nur weiter, wenn …

- Beim Einschalten wurde keine feste Helligkeit mitgegeben.

## Dann passiert …

1. Home Assistant setzt je nach Uhrzeit und Raum die oben beschriebene Standardhelligkeit.

## So kannst du reagieren

Die gewünschte Helligkeit am Wandschalter oder in Home Assistant direkt einstellen. Eine ausdrücklich gewählte Helligkeit hat Vorrang.

<div data-search-exclude markdown>

??? info "Technik für Max"

    | Feld | Wert |
    |---|---|
    | Ursprünglicher Name | Licht Standardhelligkeit bei Einschalten |
    | Home-Assistant-ID | `1777792801744` |
    | Modus | `queued` |
    | Kategorie | Licht & Präsenz |
    | Verwendete Entities | Bad (`light.bad`), Diele (`light.diele`), Flur (`light.flur`), Hue white schlafzimmer decke (`light.hue_white_schlafzimmer_decke`), Kronleuchter flur (`light.kronleuchter_flur`), Lidl led panel bad (`light.lidl_led_panel_bad`), Schlafzimmer (`light.schlafzimmer`) |

</div>

<p class="page-status">Definition aus Backup vom 12. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
