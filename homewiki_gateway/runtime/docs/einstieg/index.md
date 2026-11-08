# In wenigen Minuten zurechtfinden

Dieses Wiki ist die Anleitung für dein Zuhause. Es erklärt gespeicherte Einstellungen aus Home Assistant. Es schaltet keine Geräte und zeigt nicht, ob gerade ein Licht brennt oder ein Fenster offen ist.

## Was möchtest du wissen?

| Ich möchte … | Hier steht es |
|---|---|
| wissen, was bei einem Ausfall zu tun ist | [Notfall & Ausfälle](../notfall/index.md) |
| sehen, was in einem Raum ist | [Räume](../raeume/index.md) |
| verstehen, warum etwas von selbst passiert | [Automatische Abläufe](../automationen/index.md) |
| wissen, welche Batterie in ein Gerät gehört | [Wartung](../wartung/index.md) |
| Auto, Waschmaschine oder Garten verstehen | [Haushalt & Energie](../energie/index.md) |
| ein bestimmtes Gerät finden | [Geräte](../geraete/index.md) oder die Suche oben |
| melden, dass etwas nicht klappt | [Hilfe bei Störungen](../hilfe/index.md) |

Auf dem Handy öffnet das Menüsymbol oben links die Navigation. Die Suche findet auch einzelne Raum- und Automationsseiten. Probiere einen kurzen Namen wie „Licht“ und ergänze bei Bedarf den Raum.

Aktuelle Werte wie Batteriestände oder Geräte, die gerade nicht antworten, zeigt die Haus-Wiki-App in Home Assistant unter **Live**.

## Die wichtigsten Begriffe

| Begriff | Einfach erklärt |
|---|---|
| Home Assistant | Die zentrale Anwendung, die Geräte verbindet und Abläufe ausführt. |
| Gerät | Ein einzelnes Produkt wie eine Lampe oder ein Sensor. |
| Entität | Eine Funktion oder ein Messwert eines Geräts. Ein Gerät kann mehrere davon haben. |
| Automation | Ein Ablauf, der bei einem bestimmten Ereignis startet. |
| Auslöser | Das Ereignis, das einen Ablauf anstößt, zum Beispiel eine Uhrzeit. |
| Bedingung | Eine Voraussetzung, die zusätzlich erfüllt sein muss. |
| Aktion | Das, was der Ablauf anschließend tut. |
| Szene | Gespeicherte Einstellungen für mehrere Funktionen, die gemeinsam angewendet werden. |
| Dashboard | Eine Bedienoberfläche in Home Assistant mit Anzeigen und Schaltflächen. |
| Backup | Eine Sicherung zu einem bestimmten Zeitpunkt. Daraus entsteht dieses Wiki. |
| Integration | Die Verbindung von Home Assistant zu einem Hersteller oder Dienst, zum Beispiel Sonos oder Nuki. |
| Zigbee | Ein Funkstandard für Lampen, Schalter und Sensoren. Geräte am Strom leiten die Signale weiter. |

## Eine Automationsseite lesen

Zuerst steht dort, was du im Alltag bemerkst. Danach folgen Auslöser, Voraussetzungen und Aktionen. Mehrere Auslöser sind in der Regel verschiedene Startmöglichkeiten; sie müssen nicht nacheinander eintreten. Bei Voraussetzungen kann die tatsächliche Definition unterschiedliche Verknüpfungen enthalten. Die Kurzbeschreibung ersetzt deshalb keine technische Prüfung komplexer Abläufe.

Der Abschnitt „So kannst du reagieren“ gibt allgemeine Hinweise. Eingeklappte technische Details sind für die Administration gedacht.

## Wie aktuell ist das?

Der **Backup-Stand** nennt den Zeitpunkt der ausgewerteten Sicherung. Spätere Änderungen werden erst sichtbar, wenn ein neueres Backup verarbeitet wurde. „Im Backup hinterlegt“ bedeutet nicht automatisch „gerade eingeschaltet“ oder „funktioniert einwandfrei“.

Fehlt eine Information, ist sie möglicherweise nicht gespeichert oder nicht eindeutig auswertbar. Bitte die Administration um eine Ergänzung, anstatt eine Zuordnung zu vermuten.
