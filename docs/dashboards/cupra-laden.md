# Dashboard „Cupra Laden“

Dieses Dashboard fasst die Ladevorgänge des Cupra zusammen. Es steuert die Wallbox nicht direkt, sondern wertet Messwerte und gespeicherte Ladesitzungen aus.

<div class="annotated-image">
  <img src="../../assets/images/home-assistant/08-cupra-laden.png" alt="Oberer Bereich des Cupra-Laden-Dashboards">
  <span class="callout-marker" style="--x:50%;--y:27%" aria-label="Markierung 1">1</span>
  <span class="callout-marker" style="--x:50%;--y:55%" aria-label="Markierung 2">2</span>
</div>

<ol class="step-legend">
  <li>Gesamtwerte zeigen geladene Energie, Solar-/Netzanteil und daraus berechnete Kosten.</li>
  <li>Die nachfolgenden Karten zeigen Verteilung und einzelne Ladesitzungen.</li>
</ol>

<div class="annotated-image">
  <img src="../../assets/images/home-assistant/09-cupra-ladevorgaenge.png" alt="Ladevorgänge und Kosten im Cupra-Dashboard">
  <span class="callout-marker" style="--x:50%;--y:35%" aria-label="Markierung 1">1</span>
  <span class="callout-marker" style="--x:50%;--y:67%" aria-label="Markierung 2">2</span>
</div>

<ol class="step-legend">
  <li>Eine Ladesitzung wird aus Start-/Endwerten berechnet.</li>
  <li>Kosten und Anteile sind eine Auswertung. Bei Abweichungen sind Fahrzeug, Wallbox und Stromzähler maßgeblich.</li>
</ol>

## Häufige Fragen

- **Warum fehlt eine Sitzung?** Das Auto war möglicherweise noch nicht vollständig abgesteckt oder die Abschlussautomation hat noch nicht ausgelöst.
- **Warum weicht der Betrag ab?** Rundung, zeitversetzte Messwerte und der angesetzte Solarpreis können die Auswertung beeinflussen.
- **Startet dieses Dashboard das Laden?** Nein. Die zentrale Wallbox-Automation entscheidet anhand des gewünschten Ladezustands.

<p class="page-status">Cupra-Dashboard geprüft am 18. Juli 2026</p>
