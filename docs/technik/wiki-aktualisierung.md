---
search:
  exclude: true
---

# So aktualisiert sich dieses Wiki

Der vollständige Wochenlauf findet auf dem Raspberry Pi statt. Ein laufender Windows-PC ist nicht erforderlich.

## Normaler Ablauf

1. Der Pi holt ausschließlich einen geradlinig vorausliegenden Stand des privaten GitHub-Branches `main`. Ein abweichender Verlauf stoppt den Lauf.
2. Sonntags ab 06:00 Uhr sucht er im nur lesbar eingebundenen NAS-Ordner nach dem neuesten gültigen Home-Assistant-Backup.
3. Er liest ausschließlich eine feste Positivliste: Automationen, Szenen, Raum-/Geräte-/Entity-Register, das Dashboard-Verzeichnis und die bekannten Dashboard-Dateien.
4. Ein semantischer Vergleich erkennt echte Änderungen. Kommentare oder eine andere Reihenfolge lösen keine unnötige KI-Anfrage aus.
5. Nur neue oder veränderte Automationen ohne manuelle Beschreibung werden an das festgelegte OpenAI-Modell gesendet. Ohne solche Änderungen erfolgt normalerweise lediglich die kleine Guthabenprobe; bei einem reinen Dashboard-Prüfstopp entfällt auch diese.
6. Der Generator läuft zweimal. Nur identische Ergebnisse bestehen die Prüfung.
7. Geheimnissuche und strenger Website-Build müssen erfolgreich sein.
8. Der Pi überträgt nur die erzeugten Wiki-Seiten nach GitHub, baut ein neues Release und schaltet erst danach atomar auf die neue Website um.
9. Home Assistant sendet das Ergebnis als iPhone-Nachricht. Bei nicht erreichbarem Home Assistant wird die Nachricht lokal zwischengespeichert.

## Dashboard-Bilder

Dashboard-Dateien werden ohne LLM ausgewertet. Das Wiki speichert dabei nur fest hinterlegte Wiki-Namen, Sichtbarkeit, Anzahl der Ansichten, grobe Layoutarten, die Zahl der Strukturelemente und semantische Fingerabdrücke. Titel, Pfade, Karteninhalte und technische Kennungen aus Home Assistant werden nicht veröffentlicht. Ein unbekanntes Dashboard erscheint nur als neutraler Prüfhinweis.

Ändert sich ein Dashboard, stoppt die Veröffentlichung mit **Prüfung erforderlich**. Dadurch bleiben die bisherigen Bilder online, bis Max:

1. die betroffene Ansicht auf dem iPhone im Hochformat prüft,
2. veraltete Screenshots ersetzt,
3. die zugehörige Erklärung anpasst,
4. den Stand testet und in GitHub speichert,
5. genau diesen Backup-Stand mit `sudo homeassistant-wiki-approve-review` freigibt.

Eine vollautomatische Bildschirmaufnahme ist absichtlich nicht eingerichtet: Dafür müsste der Pi dauerhaft einen Home-Assistant-Benutzer samt Anmeldedaten und Browsersitzung besitzen. Die strukturelle Erkennung verhindert dennoch, dass geänderte Dashboards unbemerkt mit alten Bildern veröffentlicht werden.

Die vollständigen Beispielbilder wurden für dieses private Wiki bewusst freigegeben. Sie können reale Zustände, Termine oder Standorte zeigen; deshalb muss das GitHub-Repository privat bleiben. Zugangsdaten, Tokens und Codes dürfen trotzdem nie in einem Screenshot stehen.

## OpenAI-Guthaben

Ist das API-Guthaben erschöpft, wird dies als eigene Warnung an das iPhone gemeldet. Sachliche Änderungen werden weiterhin mit einer vorsichtigen, regelbasierten Beschreibung veröffentlicht; ein veralteter KI-Text wird dabei nicht weiterverwendet. Nur wenn die übrigen Sicherheits- oder Build-Prüfungen scheitern, bleibt der letzte Stand aktiv.

## Manueller Start

Die Home-Assistant-Automation **„System: Wiki jetzt aktualisieren“** sendet einen lokal abgesicherten MQTT-Startbefehl an den Pi. Der Pi verhindert Doppelstarts. Das Ergebnis kommt über dieselbe iPhone-Statusmeldung.

Der frühere PC-Upload per Dateisynchronisierung ist entfernt. Das verbliebene Windows-Hilfsskript startet nur noch den sicheren Dienst auf dem Pi und löscht keine Dateien auf dem Zielsystem.

## Einmalige Übernahme von Änderungen am Update-System

Ändern sich die Update-Skripte selbst, muss der neue GitHub-Stand einmalig auf dem Pi geradlinig übernommen und `wiki-weekly-install.sh` erneut ausgeführt werden. Dadurch werden Dienstskripte und die unveränderlichen Python-Runner aktualisiert. Dieser Bootstrap ist Teil einer bewussten Veröffentlichung; danach holt der installierte Wochenlauf neue freigegebene Wiki-Stände wieder selbst.

## Fehlerverhalten

- Die letzte funktionierende Website bleibt erreichbar.
- Kritische, große oder destruktiv wirkende Änderungen brauchen eine bewusste Freigabe.
- GitHub-, Backup-, Build-, Benachrichtigungs- und API-Fehler besitzen getrennte Statusmeldungen.
- Geheimnisse liegen nur in root-geschützten Dateien auf dem Pi und werden weder ins Wiki noch nach GitHub übernommen.

<p class="page-status">Wochenlauf und Dashboard-Prüfung dokumentiert am 18. Juli 2026</p>
