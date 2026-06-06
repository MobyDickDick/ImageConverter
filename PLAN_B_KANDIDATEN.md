# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-06, nach AC0414-S-Run OJ)

Die Rotation wurde reproduzierbar aus dem aktualisierten Qualitätsreview erzeugt.
Priorisiert werden zuerst nicht zufriedenstellende Einträge aus
`successed_conversions.txt`, danach kompakte Varianten aus dem vorhandenen
Diff-Inventar. Die vollständige Evidenz liegt unter
`artifacts/evaluation/conversion_quality_review_v2/`.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0130_M.jpg` | Diff-Inventar | `0.27991071` | Rechteck und Diagonalen sind als einfache bis mittlere Primitive abgrenzbar. |
| 2 | `AC0130.jpg` | Diff-Inventar | `0.23466992` | Größenverwandter Folgepunkt an der festgelegten Flächengrenze. |

`AC0414_S.jpg` wurde als partitionierter Kreis mit drei Speichen und rechter vertikaler Innenkante nachgezeichnet. Die Qualitätsmetrik sank von `0.31829609` auf `0.00360827`; der reguläre Gradient-/Glyph-Vorschlag wurde trotz niedriger Pixelmetrik wegen falscher Topologie verworfen. Die nächste Rotation beginnt mit `AC0130_M.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

Der aktualisierte Linkage-Report enthält die zwei verbleibenden aktiven Kandidaten.
Die Kreis-/Ring-Signale für `AC0130` sind `generalisiert`; `AC0130_M` ist
`nur Sonderfall`, weil Rechteck und Diagonalen zwar erkannt werden, aber noch
kein allgemeiner Rechteck-Geometry-IR-Seed zugeordnet ist.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
