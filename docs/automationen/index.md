<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. Nicht direkt bearbeiten. -->

# Was passiert automatisch?

Hier stehen nur Funktionen, die im Alltag sichtbar oder wichtig sind. Dazu gehören automatische Abläufe **und die in Home Assistant hinterlegten Tastenbelegungen**. Interne Wartungsabläufe und ausgeschaltete Tests sind weiter unten getrennt aufgeführt.

!!! tip "So liest du die Seiten"
    Jede Seite beginnt mit Status, Ort und einer Alltagserklärung. Technische Namen sind eingeklappt und werden nur für die Wartung benötigt.

## Sicherheit & Zugang

| Funktion | Ort | Worum geht es? |
|---|---|---|
| [Benachrichtigung Fensterkontakt Bad](generated/benachrichtigung-fensterkontakt-bad.md) | Bad · Erdgeschoss | Benachrichtigt beide iPhones, wenn das Badfenster 30 Minuten offen steht. |
| [Benachrichtigung Rauchmelder Büro](generated/benachrichtigung-rauchmelder-buero.md) | Büro · Erdgeschoss | Sendet Max und Meike eine zusätzliche Alarmmeldung, wenn der Rauchmelder im Büro Rauch erkennt. |
| [Benachrichtigung Speisekammer Türe](generated/benachrichtigung-speisekammer-tuere.md) | Speisekammer · Erdgeschoss | Benachrichtigt beide iPhones, wenn die Speisekammertür 30 Minuten offen steht. |
| [Haustür öffnen, wenn Max oder Meike ankommen](generated/tuer-oeffnen-wenn-max-zuhause-ankommt.md) | Flur · Erdgeschoss | Öffnet den Nuki-Öffner, wenn das iPhone von Max oder Meike nach einer Abwesenheit seit 30 Sekunden wieder als zu Hause erkannt wird. Weitere Beding… |

## Licht & Präsenz

| Funktion | Ort | Worum geht es? |
|---|---|---|
| [Automatische Standardhelligkeit](generated/licht-standardhelligkeit-bei-einschalten.md) | Bad · Erdgeschoss, Flur · Erdgeschoss, Schlafzimmer · Erdgeschoss | Setzt bei einem Einschaltbefehl ohne gewählte Helligkeit normalerweise 100 %. Im Flur, Schlafzimmer und Bad werden die Hauptlichter nachts auf 1 %… |
| [Dielenlicht um 22:00 Uhr ausschalten](generated/licht-flur-aus-22-uhr.md) | Flur · Erdgeschoss | Schaltet die Lichtgruppe „Diele“ jeden Abend um 22:00 Uhr aus. |
| [Flurlicht bei Anwesenheit einschalten](generated/praesenzmelder-flur-licht-an.md) | Flur · Erdgeschoss | Schaltet das Flurlicht bei erkannter Anwesenheit zwischen 08:00 und 18:00 Uhr mit 100 % Helligkeit ein. Außerhalb dieses Zeitfensters erfolgt derze… |
| [Lichtschalter Bad](generated/lichtschalter-bad.md) | Bad · Erdgeschoss | Reagiert auf den linken Tastendruck des Bad\-Wandschalters. Beim Einschalten wird tagsüber 100 Prozent und nachts zwischen Sonnenuntergang und Sonn… |
| [Lichtschalter Büro](generated/lichtschalter-buero.md) | Büro · Erdgeschoss | Schaltet das Bürolicht bei linkem Tastendruck des Z2M\-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt. |
| [Lichtschalter Diele Eingang](generated/lichtschalter-diele-eingang.md) | Flur · Erdgeschoss | Schaltet das Flurlicht bei linkem Tastendruck des Diele\-Eingang\-Wandschalters. Beim Einschalten wird tagsüber 100 Prozent und nachts zwischen Son… |
| [Lichtschalter Diele Wohnzimmer](generated/lichtschalter-diele-wohnzimmer.md) | Flur · Erdgeschoss | Schaltet das Flurlicht bei linkem Tastendruck des Diele\-Wohnzimmer\-Wandschalters. Beim Einschalten wird tagsüber 100 Prozent und nachts zwischen… |
| [Lichtschalter Ikea Shortcut Haustüre](generated/lichtschalter-ikea-shortcut-haustuere.md) | Flur · Erdgeschoss | Nutzt den IKEA\-Shortcut an der Haustüre als Alles\-aus\-Schalter für alle Lichter außer Büro oder als Einschalter für den Kronleuchter im Flur mit… |
| [Lichtschalter Kinderzimmer](generated/lichtschalter-spielzimmer.md) | Kinderzimmer · Erdgeschoss | Ein Druck auf die linke Taste am Wandschalter Kinderzimmer schaltet das Licht im Kinderzimmer ein oder aus. Beim Einschalten wird immer 100 Prozent… |
| [Lichtschalter Kinderzimmerflur](generated/lichtschalter-kinderzimmerflur.md) | Flur · Erdgeschoss | Schaltet das Flurlicht bei linkem Tastendruck des Wandschalters im Kinderzimmerflur. Beim Einschalten wird tagsüber 100 Prozent und nachts zwischen… |
| [Lichtschalter Küche oben](generated/lichtschalter-kueche-oben.md) | Küche · Erdgeschoss | Schaltet das Küchenlicht bei linkem Tastendruck des Z2M\-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt. |
| [Lichtschalter Küche unten](generated/lichtschalter-kueche-unten.md) | Küche · Erdgeschoss | Schaltet den Küchenflur bei rechtem Tastendruck des Z2M\-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt. |
| [Lichtschalter Schlafzimmer](generated/lichtschalter-schlafzimmer.md) | Schlafzimmer · Erdgeschoss | Reagiert auf den linken Tastendruck des Schlafzimmer\-Wandschalters. Beim Einschalten wird tagsüber 100 Prozent und nachts zwischen Sonnenuntergang… |
| [Lichtschalter Speisekammer links](generated/lichtschalter-speisekammer-links.md) | Speisekammer · Erdgeschoss | Schaltet die Speisekammer\-Beleuchtung bei linkem Tastendruck des Z2M\-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt. |
| [Lichtschalter Speisekammer rechts](generated/lichtschalter-speisekammer-rechts.md) | Speisekammer · Erdgeschoss | Schaltet den Küchenflur bei rechtem Tastendruck des Z2M\-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt. |
| [Lichtschalter Spielzimmer](generated/lichtschalter-kinderzimmer.md) | Spielzimmer · Erdgeschoss | Ein Druck auf die linke Taste am Wandschalter Spielzimmer schaltet das Licht im Spielzimmer ein oder aus. Beim Einschalten wird immer 100 Prozent H… |
| [Lichtschalter Wohnzimmer oben](generated/lichtschalter-wohnzimmer-oben.md) | Wohnzimmer · Erdgeschoss | Schaltet das Licht am Esstisch bei linkem Tastendruck des Wohnzimmer\-Wandschalters. Beim Einschalten werden 100 Prozent Helligkeit und die definie… |
| [Lichtschalter Wohnzimmer unten](generated/lichtschalter-wohnzimmer-unten.md) | Wohnzimmer · Erdgeschoss | Schaltet das Wohnzimmerlicht bei rechtem Tastendruck des Wohnzimmer\-Wandschalters. Beim Einschalten werden 100 Prozent Helligkeit und die definier… |
| [Präsenzmelder Flur Licht aus](generated/praesenzmelder-flur-licht-aus.md) | Flur · Erdgeschoss | Schaltet das Licht im Flur aus, sobald keine Anwesenheit mehr erkannt wird. |
| [Präsenzmelder Küche Licht an](generated/praesenzmelder-kueche-licht-an.md) | Küche · Erdgeschoss | Schaltet das Küchenlicht mit voller Helligkeit ein, wenn der Präsenzmelder in der Küche Belegung erkennt. |
| [Präsenzmelder Küche Licht aus](generated/praesenzmelder-kueche-licht-aus.md) | Küche · Erdgeschoss | Schaltet das Küchenlicht aus, wenn der Präsenzmelder in der Küche keine Belegung mehr erkennt. |
| [Präsenzmelder Licht Büro an](generated/praesenzmelder-licht-buero-an.md) | Büro · Erdgeschoss | Schaltet das Bürolicht ein, wenn der Präsenzmelder Belegung erkennt. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt. |
| [Präsenzmelder Licht Büro aus](generated/praesenzmelder-licht-buero-aus.md) | Büro · Erdgeschoss | Schaltet das Bürolicht aus, wenn der Präsenzmelder keine Belegung mehr erkennt. |
| [Türkontakt Speisekammer aus](generated/tuerkontakt-speisekammer-aus.md) | Speisekammer · Erdgeschoss | Schaltet das Speisekammerlicht aus, wenn die Tür geschlossen wird. |
| [Türkontakt Speisekammer ein](generated/tuerkontakt-speisekammer-ein.md) | Speisekammer · Erdgeschoss | Schaltet das Speisekammerlicht ein, wenn die Tür geöffnet wird. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt. |

## Haushalt

| Funktion | Ort | Worum geht es? |
|---|---|---|
| [Müllabfuhr Benachrichtigung Zentral](generated/muellabfuhr-benachrichtigung-zentral.md) | kein fester Raum – betrifft das ganze Haus | Sammelt alle Müllarten, die am nächsten Tag abgeholt werden, und verschickt um 18:00 eine Erinnerung zum Rausstellen der Tonnen. |
| [Spülmaschine ist fertig](generated/spuelmaschine-fertig-blueprint.md) | Küche · Erdgeschoss | Benachrichtigt Max und Meike, wenn die Spülmaschine laut gemessener Leistungsaufnahme fertig ist. |
| [Trockner ist fertig](generated/trockner-fertig-blueprint.md) | Waschküche · Keller | Benachrichtigt Max und Meike, wenn der Trockner laut Leistungsaufnahme fertig ist. |
| [Waschmaschine ist fertig](generated/waschmaschine-fertig-blueprint.md) | Waschküche · Keller | Benachrichtigt Max und Meike, wenn die Waschmaschine laut Leistungsaufnahme fertig ist. |

## Garten & Wasser

| Funktion | Ort | Worum geht es? |
|---|---|---|
| [Gartenbewässerung täglich um 09:00 Uhr](generated/bewaesserung-urlaub.md) | Garten · Außenbereich | Wenn diese Automation eingeschaltet ist, öffnet sie das Gartenventil jeden Tag um 09:00 Uhr für zwei Minuten. Ein Urlaubsmodus wird derzeit nicht g… |
| [Lichtschalter Garten oben](generated/lichtschalter-garten-oben.md) | Garten · Außenbereich | Schaltet die Terrassenbeleuchtung bei linkem Tastendruck des Garten\-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt. |
| [Lichtschalter Garten unten](generated/lichtschalter-garten-unten.md) | Garten · Außenbereich | Schaltet die Lounge\-Beleuchtung bei rechtem Tastendruck des Garten\-Wandschalters. Beim Einschalten wird immer 100 Prozent Helligkeit gesetzt. |
| [Pflanzenerinnerung](generated/pflanzenerinnerung.md) | kein fester Raum – betrifft das ganze Haus | Erinnert am 1. und 14. jedes Monats um 13:00 Uhr ans Gießen und wiederholt die Erinnerung alle 3 Stunden, bis der Gießkannen\-Helfer zurückgesetzt… |
| [Wasser Garten für 1h an](generated/wasser-garten-fuer-1h-an.md) | Garten · Außenbereich | Schaltet das Garten\-Wasserventil per Helfer\-Taste für 1 Stunde ein, sofern es aktuell ausgeschaltet ist. |
| [Wasser Garten für 2h an](generated/wasser-garten-fuer-2h-an.md) | Garten · Außenbereich | Schaltet das Garten\-Wasserventil per Helfer\-Taste für 2 Stunden ein, sofern es aktuell ausgeschaltet ist. |
| [Wasser Garten für 30min an](generated/wasser-garten-fuer-30min-an.md) | Garten · Außenbereich | Schaltet das Garten\-Wasserventil per Helfer\-Taste für 30 Minuten ein, sofern es aktuell ausgeschaltet ist. |
| [Wasserventil nach 2h aus](generated/wasserventil-nach-2h-aus.md) | Garten · Außenbereich | Schaltet das Garten\-Wasserventil 2 Stunden nach dem Einschalten automatisch wieder aus. |

## Energie & Auto

| Funktion | Ort | Worum geht es? |
|---|---|---|
| [Auto\-Laden Zusammenfassung \(Push\)](generated/auto-laden-zusammenfassung-push.md) | Garage · Außenbereich | Sendet Max nach dem Vollladen oder Abstecken eine Zusammenfassung zu geladener Energie, Solar- und Netzanteil sowie durchschnittlichem Preis. |
| [Batterie\-Warnung täglich 09:00 \(&lt; 30%, ohne Mobile\-App\)](generated/batterie-warnung-taeglich-09-00-lt-30-ohne-mobile-app.md) | kein fester Raum – betrifft das ganze Haus | Prüft täglich um 09:00 alle Batterie\-Sensoren unter 30 Prozent, ignoriert Mobile\-App\-Geräte und sendet für jedes betroffene Gerät eine Push\-Nac… |
| [Ladebeginn an Max melden](generated/wallbox-benachrichtigung.md) | Garage · Außenbereich | Informiert Max, wenn die Wallbox aktiv lädt, das Auto angeschlossen ist und noch nicht voll geladen wurde. |
| [Laden bei Anwesenheit anbieten](generated/wallbox-benachrichtigung-2.md) | Garage · Außenbereich | Informiert Max über den aktuellen Strompreis, wenn das Auto zuhause, aber noch nicht angesteckt und nicht voll geladen ist. |
| [Wallbox Zentrale Steuerung](generated/wallbox-zentrale-steuerung.md) | Garage · Außenbereich | Steuert die Wallbox abhängig vom Zielstatus: Sicherheitsladen und preisoptimiertes Laden erzwingen das Laden; Warten und Voll geladen stoppen das L… |

??? info "Ausgeschaltete Automationen"

    - [System \- Recorder täglich auf 30 Tage begrenzen](generated/system-recorder-taeglich-auf-30-tage-begrenzen.md) – Ausgeschaltet, weil Home Assistant die Aufbewahrungsdauer bereits selbst verwaltet.
    - [System \- Recorder wöchentlich repacken](generated/system-recorder-woechentlich-repacken.md) – Ausgeschaltet; dieser zusätzliche Wartungsschritt ist derzeit nicht erforderlich.
    - [Wallbox Override Reset](generated/wallbox-override-reset.md) – Die früher verwendete Wallbox-Override-Funktion existiert nicht mehr. Diese Automation bleibt deshalb ausgeschaltet.

??? info "Technische Wartungsabläufe (nicht für den Alltag)"

    - [Auto\-Laden Session Start \(Snapshot\)](generated/auto-laden-session-start-snapshot.md)
    - [Pflanzenerinnerung Helfer](generated/pflanzenerinnerung-helfer.md)
    - [System \- Recorder Diagnosewerte täglich bereinigen](generated/system-recorder-diagnosewerte-taeglich-bereinigen.md)
    - [Tibber API Timer](generated/tibber-api-timer.md)
    - [Tibber Reload](generated/tibber-reload.md)

## Szenen

Eine Szene stellt mehrere Geräte gemeinsam auf gespeicherte Werte.

- **Filmabend:** Schaltet die drei aktuell hinterlegten Wohnzimmerlichter in die gespeicherte Filmabend-Stimmung.

<p class="page-status">Definitionen aus Backup vom 15. Juli 2026; Status und dauerhafte Ergänzungen geprüft am 13. Juli 2026</p>
