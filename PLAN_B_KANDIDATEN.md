# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-06, nach AC0835-L-Run OH)

Die Rotation wurde reproduzierbar aus dem aktualisierten Qualitätsreview erzeugt.
Priorisiert werden zuerst nicht zufriedenstellende Einträge aus
`successed_conversions.txt`, danach kompakte Varianten aus dem vorhandenen
Diff-Inventar. Die vollständige Evidenz liegt unter
`artifacts/evaluation/conversion_quality_review_v2/`.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0922_S.jpg` | Diff-Inventar | `0.33015759` | Höchste Abweichung unter den kompakten, renderbaren Kandidaten. |
| 2 | `AC0414_S.jpg` | Diff-Inventar | `0.31829609` | Sehr kompakte Kreis-/Innengeometrie mit hoher Abweichung. |
| 3 | `AC0130_M.jpg` | Diff-Inventar | `0.27991071` | Rechteck und Diagonalen sind als einfache bis mittlere Primitive abgrenzbar. |
| 4 | `AC0130.jpg` | Diff-Inventar | `0.23466992` | Größenverwandter Folgepunkt an der festgelegten Flächengrenze. |

Die reale Re-Konvertierung von `AC0835_L.jpg` senkte `normalized_mse` von `0.05726039` auf `0.03911266` und damit unter die Review-Grenze. Der erledigte Kandidat wurde aus der Rotation entfernt; die nächste reguläre Rotation beginnt mit `AC0922_S.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

Der aktualisierte Linkage-Report enthält die vier verbleibenden aktiven Kandidaten. Drei
Perception-Fragen sind `generalisiert`: Kreis-/Ring-Signale für
`AC0922_S`, `AC0414_S` und `AC0130` sowie der horizontale Anschluss
von `AC0922_S`. `AC0130_M` ist `nur Sonderfall`, weil Rechteck und Diagonalen
zwar erkannt werden, aber noch kein allgemeiner Rechteck-Geometry-IR-Seed
zugeordnet ist.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
