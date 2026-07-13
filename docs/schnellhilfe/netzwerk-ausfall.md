# Internet oder WLAN ist ausgefallen

Internet und Heimnetz sind nicht dasselbe: Bei einem reinen Internetausfall können Home Assistant und viele lokale Automationen weiterlaufen. Bei einem WLAN- oder Routerausfall sind zusätzlich App, Wiki und einzelne Funkgeräte im Heimnetz betroffen.

## Woran lässt sich der Umfang erkennen?

- **Nur Internetseiten gehen nicht:** Wahrscheinlich Internetanschluss oder Anbieter; lokale Schalter und manche Automationen können weiterlaufen.
- **Home Assistant und Wiki gehen ebenfalls nicht:** Wahrscheinlich Heimnetz/WLAN oder mehrere Geräte ohne Strom.
- **Nur ein Smartphone ist betroffen:** Zuerst WLAN dieses Smartphones prüfen.

## Sichere erste Schritte

1. Mit einem zweiten Gerät prüfen, ob WLAN und Internet betroffen sind.
2. Kontrollieren, ob andere Geräte im Haus Strom haben.
3. Router und Netzwerkgeräte nur anhand ihrer Kontrollleuchten prüfen.
4. Nicht Router, NAS, Thin Client und Raspberry Pi gleichzeitig neu starten.
5. Beginn und Umfang des Ausfalls notieren und Max informieren.

## Was währenddessen fehlen kann

Sprachassistenten, Internetdaten, Nachrichten von unterwegs und die Fernbedienung außerhalb des Hauses können ausfallen. Sicherheit und Zugang deshalb direkt vor Ort prüfen und nicht allein auf eine App-Anzeige vertrauen.

!!! info "Noch nicht sicher bekannt"
    Routermodell, physischer Routerstandort und freigegebene Neustartreihenfolge sind nicht in Home Assistant hinterlegt. Das Wiki erfindet diese Angaben nicht.

<p class="page-status">Geprüft: 13. Juli 2026</p>
