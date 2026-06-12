# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-12, Plan-B Run PG)

`AC0722_1_S` wird jetzt mit dem bereits für die große Variante eingeführten
beschreibungsgetriebenen `LeftRotatedSquareKelleTGlyph` rekonstruiert. Die
allgemeine Rasterregistrierung transformiert nun neben Linien und Text auch den
`body_bbox` des Quadratgrundkörpers, sodass dieselbe semantische Topologie auf
die kleine Variante skaliert werden kann.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0845_S.jpg` | Diff-Inventar | `0.04927739` | Kleines kreisförmiges rH-Badge, dessen Alt-SVG fälschlich eine Außenleitung enthält. |

Die nächste reguläre Rotation beginnt mit `AC0845_S.jpg`. Der reproduzierbare
Review findet derzeit keinen weiteren qualifizierten Diff-Fall oberhalb der
Review-Grenze.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält nur noch `AC0845_S`; PF8 erkennt dort
einen allgemeinen `CircleBackground`-Seed und entscheidet `generalisiert`,
während die Text-Glyph-Erkennung Gegenstand des nächsten Plan-B-Pakets bleibt.
`AC0722_1_S` ist nicht mehr aktiv: Die reale Konvertierung bestätigt die
allgemeine beschreibungsgetriebene Rechteck-/Linien-/Text-Topologie der
AC0722-Familie, ohne einen variantenspezifischen Perception-Sonderfall.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
