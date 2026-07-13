# Urlaub

## Vor der Abreise

- [ ] Türen und Fenster selbst prüfen
- [ ] Kritische Haushaltsgeräte und Wasserstellen prüfen
- [ ] Gewünschte Handy-Benachrichtigungen testen
- [ ] Klären, wer bei einer Rauch-, Fenster- oder Gerätewarnung reagieren kann
- [ ] Gartenbewässerung bewusst prüfen

## Kein zentraler Urlaubsmodus

Im aktuellen System wurde kein Schalter gefunden, der das ganze Haus zuverlässig in einen Urlaubsmodus versetzt. Daher keinen solchen Gesamtzustand voraussetzen.

!!! warning "Die Gartenbewässerung läuft täglich"
    Die in Home Assistant noch „Bewässerung Urlaub“ genannte Automation ist aktiv und öffnet das Gartenventil **jeden Tag um 09:00 Uhr für zwei Minuten**. Sie prüft keinen Urlaubsmodus. Wenn das nicht gewünscht ist, muss die Automation in Home Assistant ausgeschaltet werden. Nach einer manuellen Betätigung immer prüfen, ob das Ventil wieder geschlossen ist.

[Details zur Gartenbewässerung](../automationen/generated/bewaesserung-urlaub.md)

## Nach der Rückkehr

Prüfen, ob Warnmeldungen vorliegen, ob das Gartenventil geschlossen ist und ob zuvor bewusst ausgeschaltete Automationen wieder benötigt werden. Nichts vorsorglich neu koppeln oder zurücksetzen.

<p class="page-status">Mit Home Assistant abgeglichen: 13. Juli 2026</p>
