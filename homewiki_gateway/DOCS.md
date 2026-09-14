# Haus-Wiki

Haus-Wiki erzeugt aus dem neuesten vollständigen Home-Assistant-Backup eine verständliche, lokal gehostete Dokumentation. Das Wiki ist ausschließlich über Home Assistant Ingress erreichbar.

## Ersteinrichtung

1. Binde das NAS in Home Assistant zusätzlich als Netzwerkfreigabe mit dem Namen `HausWiki` ein.
2. Hinterlege unter **Konfiguration** den Verschlüsselungscode deiner Home-Assistant-Backups.
3. Starte die App und öffne **Haus-Wiki** in der Seitenleiste.
4. Wähle **ChatGPT anmelden** und schließe die Device-Code-Anmeldung mit dem ChatGPT-Konto ab.
5. Starte einmal **Jetzt aktualisieren**. Danach laufen Aktualisierungen automatisch.

## Verhalten

- Standardplan: Mittwoch und Sonntag um 02:00 Uhr in der Home-Assistant-Zeitzone.
- Das neueste Vollbackup wird über die Supervisor-API ausgewählt, auch wenn es auf einem Netzwerkspeicher liegt.
- Während eines laufenden Backups wartet Haus-Wiki.
- Ohne lesbares Vollbackup wird die aktive Wiki-Version nicht verändert.
- Ohne wiki-relevante Änderungen wird nicht neu gebaut; Home Assistant erhält trotzdem eine Meldung.
- Codex benötigt keine Freigaben. Das LLM sieht ausschließlich eine bereinigte, auf Wiki-Fakten begrenzte Struktur.
- Bei LLM-Fehlern wird die deterministische Dokumentation veröffentlicht. Bei ausgeschöpftem ChatGPT-Kontingent bleibt die alte Version aktiv und der Lauf wartet auf einen späteren Neuversuch.
- Erfolgreiche Versionen werden nach `/share/HausWiki` exportiert und können in der Oberfläche zurückgerollt werden.

## Authentifizierung

`llm_provider: chatgpt` verwendet den im Container installierten offiziellen Codex-CLI und eine Device-Code-Anmeldung. `llm_provider: api` verwendet den optional hinterlegten API-Key. `disabled` schaltet LLM-Ergänzungen ab.

Codex-Anmeldedaten liegen unter `/data/codex-home`, werden nicht protokolliert und bewusst nicht in Home-Assistant-Backups aufgenommen. Nach einer Wiederherstellung ist eine erneute Anmeldung erforderlich.

## Manuelle Seiten

Nur die in `admin_users` eingetragenen Home-Assistant-Benutzernamen dürfen Läufe starten, Rollbacks ausführen, die ChatGPT-Anmeldung verwalten oder manuelle Seiten bearbeiten. Manuelle Seiten liegen getrennt unter `/data/manual` und werden vom Generator sowie vom LLM niemals verändert.

## Updates

Neue Versionen werden als `amd64`- und `aarch64`-Container über GitHub Container Registry veröffentlicht. Aktiviere in Home Assistant **Automatisch aktualisieren**, damit beim nächsten Wiki-Lauf bereits die aktuelle App-Version verwendet wird.
