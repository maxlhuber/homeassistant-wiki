# Unser Zuhause

Dieses Wiki erklärt unser Smart Home in normaler Sprache. Es zeigt, **was automatisch passiert**, **wo ein Gerät steht** und **was bei einer Störung zu tun ist**. Das Wiki selbst steuert nichts – dafür läuft Home Assistant auf dem Thin Client.

!!! tip "Neu hier?"
    [Hier starten, Meike](meike/index.md) ist der persönliche Einstieg für die tägliche Bedienung. Die [bebilderte Home-Assistant-Anleitung](bedienung/index.md) erklärt anschließend jeden wichtigen Bildschirm.

!!! danger "In einem echten Notfall"
    Bei Feuer, Rauch, Gasgeruch, einem medizinischen Notfall oder Einbruch nicht zuerst Home Assistant untersuchen. Menschen in Sicherheit bringen und den passenden Notruf wählen.

## Schnell ans Ziel

<div class="grid cards" markdown>

-   :material-lifebuoy:{ .lg .middle } **Etwas funktioniert nicht**

    ---

    Die [Schnellhilfe](schnellhilfe/index.md) führt ohne Fachbegriffe durch die ersten Prüfungen.

-   :material-information-outline:{ .lg .middle } **Wie funktioniert das alles?**

    ---

    [So funktioniert unser Smart Home](grundlagen.md) erklärt Home Assistant, Automationen und die drei beteiligten Computer.

-   :material-view-dashboard:{ .lg .middle } **Was zeigt welches Dashboard?**

    ---

    Die [Dashboard-Anleitung](dashboards/index.md) erklärt Übersicht, Cupra, Karte und Systemstatus mit Bildern.

-   :material-floor-plan:{ .lg .middle } **Was steht wo?**

    ---

    Unter [Räume](raeume/index.md) und [Geräte](geraete/index.md) stehen Aufgabe, Standort und eine mögliche manuelle Alternative.

-   :material-robot:{ .lg .middle } **Was passiert von selbst?**

    ---

    Unter [Automationen](automationen/index.md) steht für jede Funktion: Auslöser, Wirkung, Ort und Reaktion bei einem Fehler.

</div>

## Die drei wichtigsten Systeme

| System | Aufgabe | Wenn es ausfällt |
|---|---|---|
| Home-Assistant-Thin-Client | Steuert Geräte und Automationen | Automationen und App-Bedienung können ausfallen |
| Raspberry Pi | Zeigt nur dieses Wiki | Das Smart Home läuft weiter; nur die Anleitung ist nicht erreichbar |
| WD-NAS | Bewahrt Sicherungen auf | Der laufende Betrieb geht zunächst weiter; neue Sicherungen können fehlen |

## Wichtige Regeln

1. Bei einem einzelnen Problem zuerst den normalen Schalter oder die direkte Gerätebedienung versuchen.
2. Kein unbekanntes Gerät löschen, neu koppeln oder auf Werkseinstellungen zurücksetzen.
3. Eine App-Meldung ergänzt Rauchmelder, Türschloss und andere Sicherheitseinrichtungen – sie ersetzt sie nicht.
4. Bei Unsicherheit den Zeitpunkt und die Beobachtung notieren und Max informieren.

<p class="page-status">Mit Home Assistant abgeglichen: 18. Juli 2026</p>
