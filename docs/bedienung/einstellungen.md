# Einstellungen verstehen

Die Einstellungen zeigen, wie Home Assistant aufgebaut ist. Meike darf hier selbstverständlich nachsehen. Änderungen an Geräten, Integrationen, Automationen, Apps, Backups und Dashboards übernimmt im Zweifel Max, weil eine einzelne Löschung mehrere Automationen betreffen kann.

<div class="guide-image">
  <img src="../../assets/images/home-assistant/13-einstellungen.png" alt="Startseite der Home-Assistant-Einstellungen">
</div>

Auf dieser Startseite führt **Home Assistant Cloud** zum sicheren Zugriff von unterwegs. **Geräte & Dienste** enthält Integrationen, Geräte, einzelne Werte und Helfer. Unter **Automationen & Szenen** liegen die Wenn-dann-Regeln und gespeicherten Lichtstimmungen. **Dashboards** verwaltet die sichtbaren Bedienoberflächen.

## Geräte & Dienste

<div class="guide-image">
  <img src="../../assets/images/home-assistant/15-geraete-dienste.png" alt="Geräte und Dienste in Home Assistant">
</div>

Die Reiter am unteren Rand trennen **Integrationen**, **Geräte**, **Entitäten** und **Helfer**. Ein Gerät ist der physische Gegenstand; Entitäten sind dessen einzelne Funktionen und Messwerte. Ein Temperatursensor kann beispielsweise Temperatur, Luftfeuchte und Batterie als drei Entitäten besitzen.

**Neu laden**, **Löschen**, **Gerät entfernen**, **Neu konfigurieren** oder **Integration ignorieren** kann Geräte und Automationen zumindest zeitweise trennen. Diese Aktionen bitte nur nach Rücksprache mit Max verwenden.

## Automationen & Szenen

<div class="guide-image">
  <img src="../../assets/images/home-assistant/14-automationen-szenen.png" alt="Automationen und Szenen in Home Assistant">
</div>

Mit den Reitern am unteren Rand wechselst du zwischen Automationen, Szenen, Skripten und Blueprints. Ein sichtbarer Schalter an einer Regel aktiviert oder deaktiviert sie sofort; nur verwenden, wenn klar ist, welche Funktion dadurch ausfällt.

Die verständliche Beschreibung jeder Regel steht im Wiki unter [Was passiert automatisch?](../automationen/index.md).

## Backups

<div class="guide-image">
  <img src="../../assets/images/home-assistant/16-backups.png" alt="Backup-Bereich von Home Assistant">
</div>

Hier sieht man die Sicherungsorte, Kategorien und vorhandenen Backups. **Wiederherstellen** verändert das laufende System grundlegend und gehört ausschließlich in eine geplante Reparatur durch Max.

## Home Assistant Cloud

<div class="guide-image">
  <img src="../../assets/images/home-assistant/17-cloud-fernzugriff.png" alt="Home Assistant Cloud für den Fernzugriff">
</div>

„Verbunden“ bedeutet, dass die App den vorgesehenen Cloud-Zugang von unterwegs verwenden kann.

Das Wiki bleibt unabhängig davon zunächst nur im Heimnetz erreichbar.

<p class="page-status">Einstellungsübersicht geprüft am 18. Juli 2026</p>
