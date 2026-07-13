---
search:
  exclude: true
---

# Änderungsverlauf

Hier werden inhaltlich wichtige Änderungen am Wiki festgehalten. Kleine Rechtschreibkorrekturen müssen nicht einzeln aufgeführt werden.

## 13. Juli 2026

- Familienansicht vollständig überarbeitet: verständlicher Einstieg, Grundlagen und konkrete Schnellhilfe statt leerer Vorlagen
- Gerätebestand auf alltagsrelevante physische Geräte reduziert; Diagnosewerte, interne Dienste, virtuelle Gruppen und erkennbare Duplikate ausgeblendet
- Räume, Geräte und Automationen um verständliche Ortsangaben, Ausfallhinweise und manuelle Reaktionsmöglichkeiten ergänzt
- Technische Entity-IDs und Wartungsdetails in einklappbare Abschnitte verschoben
- Dauerhafte Korrekturdatei eingeführt, damit bestätigte Live-Anpassungen bei späteren Backup-Importen erhalten bleiben
- Widersprüchliche Zuordnung von Kinderzimmer und Spielzimmer sichtbar gekennzeichnet, ohne eine nicht bestätigte Zuordnung zu erfinden
- Alltagstexte an den tatsächlichen Stand angepasst: kein zentraler Abwesenheits-, Schlaf- oder Urlaubsmodus; tägliche Gartenbewässerung klar benannt
- Raspberry Pi als aktiven Wiki-Server dokumentiert und Familiennavigation von Vorlagen und internen Prüflisten bereinigt
- Veröffentlichung auf atomare Releases mit lokalem und entferntem Strict-Build umgestellt; ein fehlerhafter Build lässt den bisherigen Live-Stand bestehen
- Zugriff von unterwegs als noch nicht eingerichtet gekennzeichnet; keine ungeschützte Portfreigabe vorgesehen
- Geschützte Vollsicherung vor den Änderungen lokal erstellt (`8086f527`) und fertigen Stand anschließend vollständig auf dem NAS gesichert (`c88e8807`, einschließlich Datenbank)
- Rauchmelder im Büro benachrichtigt jetzt Max und Meike; ein fehlgeschlagener Versand blockiert den jeweils anderen nicht
- Spülmaschinen-Fertigmeldung an Max und Meike erweitert und beide Versandwege voneinander entkoppelt
- Einheit in der Wallbox-Ladebenachrichtigung von `€/kWh` auf `ct/kWh` berichtigt
- Beschreibungen der Flurlicht- und Standardhelligkeits-Automationen an das tatsächliche Verhalten angepasst
- Nicht mehr vorhandene beziehungsweise deaktivierte Geräte aus der Szene „Filmabend“ entfernt
- Nicht benötigte zusätzliche Recorder-Bereinigungen ausgeschaltet; der bereits ausgeschaltete Wallbox-Override-Reset bleibt wegen einer fehlenden Entity aus
- Automationen und Szenen neu geladen; Home-Assistant-Konfigurationsprüfung erfolgreich, keine offenen Reparaturhinweise
- Lichtautomationen für Kinderzimmer und Spielzimmer mit dem aktuellen Live-Stand abgeglichen: Schalter- und Lichtnamen passen jetzt funktional zusammen; die vertauschten Gerätebereiche bleiben bis zur Prüfung vor Ort gekennzeichnet
- Geräte in Kinderzimmer und Spielzimmer neu mit Home Assistant abgeglichen; Schalter, Leuchten und Raumzuordnungen sind nun konsistent, daher wurden die bisherigen Vertauschungs-Warnungen entfernt
- Temperatursensoren abschließend eindeutig benannt und zugeordnet: je ein Sensor im Kinderzimmer und im Spielzimmer

## 12. Juli 2026

- Grundgerüst des Wikis angelegt
- Navigation und Suchfunktion vorbereitet
- Vorlagen für Automationen, Geräte und Räume erstellt
- Schnellhilfe und technische Grundstruktur vorbereitet
- Sicheren Ablauf für die Home-Assistant-Bestandsaufnahme ergänzt
- Aktuelle Home-Assistant- und Supervisor-Version aus dem NAS-Backup erfasst
- Installierte Add-ons und automatische NAS-Sicherungen dokumentiert
- 54 Automationen und 14 Räume als durchsuchbare Einzelseiten erzeugt
- Gerätebestand und Szenen aus Home Assistant übernommen
- Auffällige Sicherheits-, Beschreibungs- und Zuordnungspunkte festgehalten
