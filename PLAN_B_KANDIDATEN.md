# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-12, Plan-B Run PF)

`AC0701_1_S` wird jetzt durch ein allgemeines, beschreibungsgetriebenes
Geometry-IR aus rotem Quadratgrundkörper und unterem vertikalem Anschluss
rekonstruiert. Beide Primitive bleiben getrennt und verwenden ausschließlich
relative Koordinaten. Der reproduzierbare Review entfernt die nun grüne
Variante; der qualifizierte Diff-Pool enthält aktuell nur noch zwei Fälle
oberhalb der Review-Grenze.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0722_1_S.jpg` | Diff-Inventar | `0.05681223` | Kleine links gedrehte Quadrat-Kellen-Variante mit horizontal bleibendem T-Glyph. |
| 2 | `AC0845_S.jpg` | Diff-Inventar | `0.04927739` | Kleines kreisförmiges rH-Badge, dessen Alt-SVG fälschlich eine Außenleitung enthält. |

Die nächste reguläre Rotation beginnt mit `AC0722_1_S.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält beide aktiven Kandidaten.
`AC0722_1_S` bleibt `noch nicht erkannt`. Für `AC0845_S` erkennt PF8 einen
allgemeinen `CircleBackground`-Seed und entscheidet `generalisiert`; die
Text-Glyph-Erkennung bleibt Gegenstand des eigentlichen Plan-B-Pakets.
`AC0701_1_S` ist nicht mehr aktiv: Die reale Konvertierung belegt die
allgemeine beschreibungsgetriebene Rechteck-/Linien-Topologie, ohne dafür einen
variantenspezifischen PF8-Sonderfall einzuführen.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
