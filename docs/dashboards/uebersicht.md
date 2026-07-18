# Dashboard „Übersicht“

Die Übersicht ist die Startseite für den Alltag.

<div class="annotated-image">
  <img src="../../assets/images/home-assistant/01-uebersicht-oben.png" alt="Oberer Bereich der Übersicht">
  <span class="callout-marker" style="--x:50%;--y:8%" aria-label="Markierung 1">1</span>
  <span class="callout-marker" style="--x:50%;--y:46%" aria-label="Markierung 2">2</span>
  <span class="callout-marker" style="--x:50%;--y:57%" aria-label="Markierung 3">3</span>
  <span class="callout-marker" style="--x:50%;--y:66%" aria-label="Markierung 4">4</span>
  <span class="callout-marker" style="--x:50%;--y:82%" aria-label="Markierung 5">5</span>
</div>

<ol class="step-legend">
  <li>Personenstatus von Max und Meike sowie der Cupra-Ladestand. Personenstandorte beruhen auf der iPhone-Ortung und können verzögert sein.</li>
  <li>Die Suche findet sichtbare Home-Assistant-Elemente.</li>
  <li>Die obere Schnellstatus-Zeile zeigt eingeschaltete Lichter und offene Schlösser.</li>
  <li>Die untere Schnellstatus-Zeile zeigt offene Türen/Fenster und kritische Batterien.</li>
  <li>Wetter und Außentemperatur. Weiter unten folgen Hausgeräte, Strom, Wallbox und die Raumleiste.</li>
</ol>

## Licht, Tür/Fenster und Batterie

Ein Tipp auf eine Schnellstatus-Kachel öffnet die zugehörige Liste. Die Zahl ist die Anzahl der aktuell passenden Einträge. „Geöffnet“ bedeutet bei Tür-/Fensterkontakten nur, dass der jeweilige Kontaktsensor offen meldet.

Im geöffneten Fenster stehen zuerst die Kontakte, die gerade „offen“ melden; darunter folgen die „geschlossenen“ Kontakte. Das sagt nichts über die mechanische Verriegelung eines Schlosses aus.

## Türschloss und Türöffner richtig unterscheiden

<ol class="step-legend">
  <li>Das <strong>Nuki-Türschloss</strong> beschreibt die mechanische Verriegelung der zugehörigen Tür.</li>
  <li>Der <strong>Nuki-Türöffner</strong> bedient den elektrischen Öffner. Dessen „verriegelt/entriegelt“-Darstellung beschreibt den Betriebsmodus des Öffners, nicht zuverlässig die mechanische Verriegelung der Wohnungstür.</li>
</ol>

!!! warning "Vor dem Öffnen"
    Vor einer Fernbedienung prüfen, wer vor der Tür steht und ob das Öffnen sicher ist. Bei einem widersprüchlichen Zustand die Tür direkt kontrollieren und Schlüssel beziehungsweise Nuki-App verwenden.

## Hausgeräte, Strom und Wallbox

<div class="guide-image">
  <img src="../../assets/images/home-assistant/06-uebersicht-hausgeraete-strom.png" alt="Hausgeräte und Stromwerte auf der Übersicht">
</div>

<div class="guide-image">
  <img src="../../assets/images/home-assistant/07-uebersicht-strom-wallbox.png" alt="Strom- und Wallboxbereich auf der Übersicht">
</div>

Unter Wetter folgen:

- Status von Spülmaschine, Trockner und Waschmaschine
- aktueller Strompreis sowie aktuelle Leistungswerte
- Wallbox-Zielstatus, nächster Ladestart, Cupra-Ladestand und durchschnittlicher Ladepreis

Diese Aufnahmen sind Beispiele vom 18. Juli 2026; Werte und Zustände ändern sich laufend. Der tatsächliche Zustand am Gerät oder Fahrzeug hat bei Widersprüchen Vorrang.

<p class="page-status">Übersicht und Detailfenster geprüft am 18. Juli 2026</p>
