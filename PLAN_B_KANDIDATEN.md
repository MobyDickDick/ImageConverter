# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-07, Qualitätsrefresh Run OM)

Die neue Rotation wurde reproduzierbar aus dem aktualisierten Qualitätsreview
abgeleitet. Zuerst wird der nicht mehr zufriedenstellende Eintrag aus
`successed_conversions.txt` priorisiert; danach folgen kompakte, renderbare
Varianten aus dem Diff-Inventar.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0820_L.jpg` | erfolgreicher Altbestand | `0.05117826` | Einziger der 48 erfolgreichen Einträge oberhalb der Review-Grenze `0.04594568`. |
| 2 | `AC0531_1_S.jpg` | Diff-Inventar | `0.15610678` | Höchste verbleibende Abweichung unter den kompakten renderbaren Fällen; Rechteck, Diagonale und Mittelpunkt sind klar abgrenzbar. |
| 3 | `AC0502_1_M.jpg` | Diff-Inventar | `0.15533278` | Gedrehte Klappengeometrie mit sehr hoher Abweichung und wiederverwendbaren Rechteck-/Punkt-Primitiven. |
| 4 | `AC0551_1_M.jpg` | Diff-Inventar | `0.14916385` | Kompaktes Rechteckmotiv mit horizontalen Teilungen und mittiger Winkelkontur. |
| 5 | `AC0403_1_M.jpg` | Diff-Inventar | `0.11117438` | Sehr kompakte gedrehte Kreis-/Innengeometrie oberhalb der Review-Grenze. |

Die nächste reguläre Rotation beginnt mit `AC0820_L.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten. Vier
Fragen sind `generalisiert`: Kreis-/Ring-Erkennung für `AC0820_L` und
`AC0403_1_M` sowie allgemeine Primitive und ein Kreis-Seed für die beiden
Klappenvarianten `AC0531_1_S` und `AC0502_1_M`. `AC0551_1_M` bleibt
`nur Sonderfall`, weil Linien und Rechteck erkannt werden, aber weder ein
allgemeiner Rechteck- noch HorizontalRule-Seed vorliegt.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
