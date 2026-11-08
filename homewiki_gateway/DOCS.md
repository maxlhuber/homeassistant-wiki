# Haus-Wiki 4.0

Das Wiki erklärt das Zuhause aus dem zuletzt verarbeiteten Home-Assistant-Backup und schaltet keine Geräte. Die App hat vier Bereiche:

- **Wiki**: das Haus-Handbuch für die Familie mit Notfall & Ausfällen, Räumen, Geräten, automatischen Abläufen, Haushalt & Energie, Wartung (inklusive Batterietypen), Hilfe und einem Technik-Bereich (Integrationen, Apps, Zigbee-Netz, Netzwerk, Skripte & Helfer, Datenqualität).
- **Live**: aktuelle Werte direkt aus Home Assistant – Batteriestände, Geräte, die nicht antworten, verfügbare Updates und das Alter des letzten Backups.
- **Aktualisierung**: Status, Grundlage und Verlauf der Wiki-Läufe.
- **Verwalten**: KI-Anmeldung, eigene Anleitungen, Betriebsprotokoll und Wiederherstellung.

Mit `#live` am Ende der App-Adresse öffnet sich direkt der Bereich Live, etwa auf einem Wand-Tablet.

## Einrichtung und Zugriff

1. NAS unter Home Assistant → Einstellungen → System → Speicher als **Share** einbinden. Backup-Netzwerkspeicher sind nicht automatisch unter /share im Wiki verfügbar.
2. `export_path` auf einen eigenen Unterordner setzen, etwa `/share/NASWiki/HausWiki`. Das Wiki verwaltet diesen Unterordner vollständig. Nicht das Stammverzeichnis mit den HA-Backups als Exportziel verwenden.
3. `backup_password` mit dem Verschlüsselungscode aus dem Home-Assistant-Notfallpaket befüllen.
4. Über die HA-Seitenleiste öffnen. Ohne `admin_password` erhalten die in `admin_users` eingetragenen HA-Benutzernamen, Anzeigenamen oder Benutzer-IDs Verwaltungsrechte. Die Prüfung berücksichtigt den Anzeigenamen „Max“ unabhängig vom technischen Benutzernamen.
5. Alternativ `admin_password` konfigurieren. Dann werden Verwaltungsaktionen nach Eingabe dieses Passworts im Wiki freigeschaltet. Die Freischaltung gilt eine Stunde, ist an den HA-Benutzer gebunden und endet bei App-Neustart oder Passwortwechsel. Das Passwort wird nicht im Browser gespeichert.

Lesende Zugriffe funktionieren über Home Assistant Ingress. Direkte Zugriffe aus anderen Containern sind gesperrt; der reduzierte Health-Endpunkt bleibt für Betriebsprüfungen erreichbar.

## Aktualisierung

Standard: Mittwoch und Sonntag um 02:00 Uhr in der Home-Assistant-Zeitzone. `schedule_days`, `schedule_time` und `catch_up` steuern den Rhythmus. Ein manueller Klick meldet, ob der Lauf gestartet wurde oder bereits läuft.

Die App wartet auf laufende Supervisor-Backup-Jobs. Automatische NAS-Archive werden auf eingebundenen Share-Freigaben erkannt; andernfalls wird der Supervisor-Katalog verwendet. Nur ein lesbares und validiertes HA-Archiv kann veröffentlicht werden. Das verwendete Backup wird im Status ausgewiesen. Bei unverändertem Inhalt wird Home Assistant benachrichtigt.

Die Website wird lokal bereitgestellt und nach `export_path` exportiert. `release_retention` bestimmt die Anzahl früherer Wiki-Stände (Standard: 3). Eine Wiederherstellung ersetzt ausschließlich das Wiki. Während einer Aktualisierung ist sie gesperrt.

## OpenAI, Claude und LLM

`llm_provider` unterscheidet zwischen **OpenAI Abo**, **OpenAI API**, **Claude Abo**, **Claude API** und **Ohne KI**. OpenAI Abo startet die Device-Anmeldung des mitgelieferten Codex-CLI und verwendet dein ChatGPT-Abo. Claude Abo startet den offiziellen Claude-Code-Login; bei Claude Pro/Max erfolgt die OAuth-Bestätigung im Browser. OpenAI API und Claude API verwenden jeweils einen separat abgerechneten API-Key (`openai_api_key` bzw. `anthropic_api_key`). Die Oberfläche passt Link, Status und Schaltflächen automatisch an.

Abgelaufene Codes werden während einer aktiven Anmeldung erneuert. Wiederholte technische Fehler führen zu einem sichtbaren Fehler statt einer endlosen Anmeldeschleife. Die Anmeldung kann abgebrochen werden.

Ein fertig erzeugtes Wiki bedeutet nicht automatisch einen erfolgreichen LLM-Aufruf; fehlende Ergänzungen bleiben sichtbar. Geheimnisse werden vor LLM-Anfragen entfernt. Bei erschöpftem Kontingent wird mit `quota_retry_minutes` erneut versucht; es gibt keinen automatischen kostenpflichtigen Anbieter-Fallback. `model` ist optional (`sonnet` ist der Claude-Standard).

Codex-Zugangsdaten liegen unter `/data/codex-home`, Claude-Zugangsdaten unter `/data/claude-home`; beide Verzeichnisse sind von HA-App-Backups ausgeschlossen. Nach Wiederherstellung kann eine erneute Anmeldung nötig sein.

## Live-Werte

Der Bereich Live fragt Home Assistant höchstens einmal pro Minute über eine einzige Vorlagenabfrage ab. Handys, Uhren und Notebooks werden bei Batterien und nicht antwortenden Geräten ausgeblendet. Schwach heißt höchstens 20 %, „bald leer“ höchstens 35 %. Ein Backup älter als zwei Tage wird gelb, älter als acht Tage rot markiert. Lesen dürfen alle Home-Assistant-Benutzer, die die App öffnen können.

## Batterietypen

Für verbreitete Modelle (zum Beispiel Hue-Wandschaltermodule, IKEA-Taster, SONOFF-Wasserventil, Nuki) kennt die App den Batterietyp. Angaben sind als **Herstellerangabe** oder **typisch – bitte prüfen** gekennzeichnet. Fehlende oder abweichende Typen tragen Verwaltende im Bereich Live direkt am Gerät ein. Die Einträge liegen unter `/data/battery_types.json`, haben Vorrang vor der eingebauten Liste und erscheinen nach der nächsten Wiki-Aktualisierung auch auf der Wartungsseite samt Batterievorrat.

## Was das Wiki aus dem Backup liest

Aus dem Kernarchiv werden nur Raum-, Etagen-, Label-, Geräte- und Entitätsregister, Automationen, Szenen, Skripte, Dashboards und die Energie-Konfiguration entpackt. Aus `backup.json` werden ausschließlich die Home-Assistant-Version sowie Name, Kennung und Version jeder enthaltenen App übernommen. Integrationen werden aus den Registern abgeleitet; `core.config_entries`, `secrets.yaml`, Zugangsdaten und Verlaufsdatenbanken werden nicht gelesen. IP-Adressen, WLAN-Namen und Gerätekennungen erscheinen nicht im Wiki.

## Eigene Seiten

Eigene Anleitungen liegen getrennt unter /data/manual und werden weder vom Generator noch vom LLM überschrieben. Eine Seite mit dem Namen `notfall` wird oben auf der Notfallseite verlinkt; die Vorlage dafür enthält Felder für Kontakte, Hauptsicherung und Haupthahn. Der Editor speichert Markdown; die Veröffentlichung erfolgt mit einem erfolgreichen Backup-basierten Lauf. Keine Passwörter oder Zugangscodes in Wiki-Seiten eintragen.

## Betriebsprotokoll

Die Verwaltung zeigt Ereignisse mit Zeitpunkt, Schweregrad, Laufbezug und Verarbeitungsschritt. Dieselben Ereignisse erscheinen in den Container-Logs. Die lokalen rotierenden Dateien unter /data/logs belegen höchstens etwa 1 MB. Zugangsdaten, Device-Codes und rohe LLM-Antworten werden nicht protokolliert. Alte Läufe aus Version 2 bleiben im Verlauf erhalten; detaillierte Ereignisse werden ab Version 3 aufgezeichnet.

## Updates und interne API

Updates werden über das öffentliche GitHub-Repository und GHCR angeboten. Private Wiki-Inhalte werden nicht nach GitHub übertragen. Bestehende Optionen, eigene Seiten, Zugangsdaten und Wiki-Stände bleiben unter /data erhalten.

Die interne Oberfläche verwendet api/status, api/live, api/history, api/logs, api/manual, api/battery-types und api/auth/device/status. Schreibzugriffe benötigen Ingress, Verwaltungsrechte und den Header `X-Haus-Wiki: 1`. Dies ist keine öffentlich freizugebende API.
