# Wenn etwas nicht wie erwartet funktioniert

Das Wiki hilft beim Einordnen. Den aktuellen Gerätezustand und die Bedienung findest du in Home Assistant oder direkt am Gerät.

## Ein Gerät reagiert nicht

1. Prüfe vor Ort, welches Gerät betroffen ist und ob es Strom hat. Beachte die Bedienungsanleitung des Geräts.
2. Prüfe in Home Assistant, ob das Gerät als nicht verfügbar angezeigt wird.
3. Öffne die passende [Raumseite](../raeume/index.md) oder suche den Gerätenamen.
4. Notiere die Beobachtung und informiere die Administration. Lösche das Gerät nicht und führe keinen Werksreset durch.

## Ein automatischer Ablauf bleibt aus

1. Suche den Ablauf unter [Automationen](../automationen/index.md).
2. Prüfe, ob der beschriebene Auslöser eingetreten ist und welche Voraussetzungen gelten.
3. Notiere Uhrzeit, Raum und das erwartete Ergebnis. Ob die Automation tatsächlich eingeschaltet ist oder gestartet wurde, muss in Home Assistant geprüft werden.

## Home Assistant ist nicht erreichbar

Prüfe, ob dein Handy oder Computer mit dem richtigen Netzwerk verbunden ist. Nutze bei Bedarf die reguläre Bedienung direkt am Gerät, soweit sie dafür vorgesehen ist. Welche Funktionen ohne Home Assistant weiterlaufen, hängt vom jeweiligen Gerät ab; dieses Wiki kann das nicht live feststellen.

## Die Anleitung passt nicht zum Haus

Vergleiche zuerst den Backup-Stand mit dem Zeitpunkt der Änderung. Eine neue Einstellung kann noch fehlen. Ist die Sicherung bereits neuer, melde der Administration den Seitentitel und die unpassende Textstelle.

## Das hilft der Administration

- Betroffener Raum, Gerät oder Ablauf
- Datum und ungefähre Uhrzeit
- Was du erwartet und tatsächlich beobachtet hast
- Was du bereits geprüft hast
- Titel der Wiki-Seite und deren Backup-Stand

Zugangsdaten, PINs und private Backup-Inhalte gehören nicht in eine Fehlermeldung.

!!! warning "Bei unmittelbarer Gefahr"
    Prüfe die reale Situation und handle entsprechend. Eine App, ein Sensor oder diese Dokumentation ersetzt keine unmittelbare Hilfe bei Rauch, Wasser oder einer anderen Gefahr.
