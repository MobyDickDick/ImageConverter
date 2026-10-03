# Nächstes Arbeitspaket – ZG7.2 End-SVG-Metrikvertrag (2026-10-03)

Dieses Paket setzt nach ZG7.1 den zweiten Schritt der dokumentierten Folge
`ZG7.1 → ZG7.2 → ZG7.3 → ZG7.4 → ZG7.5 → ZG7.6` um. Es bewertet nicht den
technischen Exit des Konverters, sondern ausschließlich dessen gespeichertes,
erneut gerastertes End-SVG.

## Versionierter Vertrag

`tools/evaluate_semantic_only_quality.py` erzeugt Records des Schemas
`semantic_only_quality_report_v1`. Pflichtmetriken sind:

- mittlerer normierter Kanalfehler (`error_per_pixel`),
- symmetrische Kantenausrichtung (`edge_alignment`),
- schlechteste Objektmasken-IoU (`object_mask_iou`),
- Anschlusskontinuität (`connector_continuity`),
- Vollständigkeit der erwarteten Primitivsemantik (`semantic_score`) und
- Übereinstimmung der Canvas-Dimensionen (`dimension_match`).

Zusätzlich enthält der Record je zusammenhängendem Referenzobjekt Bounding
Box, Pixelzahl, Trefferzahl und IoU sowie die Bounding Box der gesamten
sichtbaren Fehlerregion. Kann eine Pflichtmetrik wegen eines ungültigen SVGs,
fehlender Abhängigkeit oder nicht numerischer Dimension nicht bestimmt werden,
lautet der Status `not_reachable`; alle Pflichtmetriken bleiben dann explizit
`null`. Ein erfundener Null- oder Passwert ist ausgeschlossen.

Der ZG7.1-Runner hängt denselben Record an jeden Wiederholungslauf und übernimmt
die erste Messung als Fallzusammenfassung. Damit bleibt die Rename-/Stabilitäts-
Provenienz erhalten, während die Qualität getrennt sichtbar wird.

## Kalibrierung und Fehlerproben

Die fokussierte Testsuite erzeugt ein PNG durch Rasterung eines synthetischen
Kreis/Text/Anschluss-SVGs und bewertet anschließend genau dieses gespeicherte
SVG. Alle sechs Metriken erreichen dabei ihren Idealwert. Drei unabhängige
Negativproben belegen die Zuständigkeit der Metriken:

1. Canvasbreite 32 statt 64 senkt `dimension_match` auf `0.5`,
2. entfernter Text senkt ausschließlich die erwartete Primitivsemantik und
3. ein vom Kreis abgerückter Anschluss senkt `connector_continuity`.

Ein nicht parsebares SVG belegt zusätzlich den `not_reachable`-/`null`-Pfad.

## Realer Drei-Fälle-Befund und nächster Schritt

Der reproduzierte ZG7.1-Lauf liegt als
`artifacts/evaluation/semantic_only_quality_report_v1/report_2026-10-03.json`
vor. Alle drei Fälle bleiben deterministisch und dimensionsgetreu, die neuen
Messungen verhindern aber ein falsches Qualitätsurteil: Die aktuellen End-SVGs
verfehlen die beschriebenen Primitive (`semantic_score=0.0`) und zeigen große
Pixel-, Kanten- und Maskenabstände. Die technische Stabilität aus ZG7.1 ist
damit ausdrücklich keine gute Lösung.

ZG7.2 ist abgeschlossen. Das nächste dokumentierte Paket ist **ZG7.3 –
Constraint-Fusion und Hypothesen-Beam**. Gemäß Entscheidungspunkt ist die
fehlende Primitivsemantik vor Pixel- oder Antialiasing-Feintuning zu beheben.
