# Frühere Versuche im Formmodellvergleich

Der Kreis-Pfeil-Pfad wählt weitere Versuche jetzt anhand seiner bisherigen
Messungen. Die erste Probe und die späteren Verfeinerungen setzen denselben
Suchiterator fort. Damit bleiben geprüfte Parameter, schlechte Ergebnisse und
Renderfehler im lokalen Cache erhalten. Äquivalente SVGs verschiedener Modelle
teilen ihre Renderdaten; identische Raster teilen ihre Qualitätsmessung.

Jedes verfügbare Modell erhält eine kurze Probe. Danach bestimmen
Vordergrundflächen, Kantenübereinstimmung, Pixelfehler und gemessener Fortschritt
die nächsten Suchrunden. Wiederkehrende Erkundungsrunden verhindern, dass ein
anfangs schlechteres Modell ausgeschlossen wird. Ein Modell ohne mindestens ein
Prozent Verbesserung von Formscore oder Pixelfehler während eines vollständigen
Koordinatendurchlaufs wird beendet. Bereits bestandene Modelle werden auch nach
zwei Suchrunden ohne nennenswerte Verbesserung ihres Formscores verlassen.

Die lokale Parametersuche optimiert weiterhin ihren bisherigen Pixelfehler.
Die zusätzliche Formbewertung steuert die Verteilung der Suchrunden. Nur
semantisch geprüfte Kandidaten dürfen gewinnen; ein bestandener Pixelvergleich
hat Vorrang vor einem nicht bestandenen Kandidaten. Innerhalb dieser Gruppen
entscheidet weiterhin der Pixelfehler. Kleine Verbesserungen eines weiterhin
schlechten Modells gelten nicht automatisch als erfolgreiche Konvertierung.

## Prüfungen

- 125 Tests für Formmodelle, gefüllte Symbole, Suchscheduler, Suchbots und beide
  Pfeilrichtungen bestanden. Nach der letzten Anpassung an den Abbruch bei
  stagnierender Qualität bestanden erneut alle 65 betroffenen Formmodell- und
  Pfeiltests.
- Die gezielten Tests prüfen die Fortsetzung ohne erneutes Rendern der Probe,
  eine durch Probeergebnisse geänderte Suchreihenfolge, wiederkehrende
  Erkundung, geteilte Renderdaten, den Abbruch optisch unveränderter Fehlversuche,
  verbindliche Semantik sowie gemeinsame Render- und Zeitgrenzen.
- Der bestehende Regressionstest für ein vergrößertes und verschobenes Symbol
  deckte einen zu frühen Abbruch auf. Ein Modell wird deshalb nicht wegen eines
  vorübergehenden Kantenplateaus beendet, solange sein Pixelfehler noch deutlich
  sinkt. Dieser Test besteht wieder.

## Katalogmessung und Grenzen

Die eingefrorene Stichprobe bleibt in beiden Varianten bei fünf bestandenen
von sieben Kreis-Pfeil-Fällen. Die zwei nicht unterstützten Eingaben bleiben
nicht unterstützt. Der Vergleich belegt damit keine höhere Erfolgsquote.

| Kreis-Pfeil-Stichprobe | Bisherige feste Reihenfolge | Suche mit Versuchsgedächtnis |
| --- | ---: | ---: |
| Bestandene Fälle | 5 / 7 | 5 / 7 |
| Renderings | 829 | 1081 |
| Suchzeit | 6,80 s | 15,00 s |

Die zusätzliche Bewertung und die längere Verfeinerung kosten in dieser Messung
mehr Zeit. Der Pixelfehler sinkt bei allen fünf bestandenen Fällen; die
Kantenübereinstimmung verbessert sich bei drei und verschlechtert sich bei zwei
leicht. Eine allgemein bessere oder schnellere Konvertierung ist nicht belegt.
Bei den unveränderten Kontrollfittern schwankt außerdem AC0800_M durch seinen
zeitabhängigen Abbruch; insgesamt wurden im Vergleich 7/11 beziehungsweise
6/11 Fälle bestanden. AP 2 bleibt deshalb hinsichtlich seiner Katalogabnahme
offen.

Nachweise: [feste Reihenfolge](../artifacts/evaluation/adaptive_form_models_v1/history_fixed_order_control.json),
[aktueller Lauf](../artifacts/evaluation/adaptive_form_models_v1/history_guided_isolated.json),
[Vergleichsimplementierung](../artifacts/evaluation/adaptive_form_models_v1/history_fixed_order_control.py)
und [Quellhashes](../artifacts/evaluation/adaptive_form_models_v1/history_sources.json).
Die frühere Vergleichsimplementierung wurde für den Kontrolllauf rekonstruiert;
die Bildpixel, Beschreibungen, Renderer, Prüfungen und Budgets bleiben gleich.

Das Gedächtnis gilt innerhalb eines Formmodellvergleichs. Es lädt keine
Ergebnisse früherer Konvertierungsstarts und lernt keine Rangfolge über mehrere
Bilder. Außerdem kann es nur zwischen den tatsächlich angebotenen Modellen
wechseln: Der Kreis-Pfeil-Pfad bietet derzeit zwei und drei Verlaufsstützpunkte
derselben Grundgeometrie. Andere Konstruktionen für weitere Formfamilien sowie
ein dauerhaftes Gedächtnis für frühere Konvertierungsstarts bleiben ausstehend.
