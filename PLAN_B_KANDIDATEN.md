# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-06, nach AC0922-S-Run OI)

Die Rotation wurde reproduzierbar aus dem aktualisierten Qualitätsreview erzeugt.
Priorisiert werden zuerst nicht zufriedenstellende Einträge aus
`successed_conversions.txt`, danach kompakte Varianten aus dem vorhandenen
Diff-Inventar. Die vollständige Evidenz liegt unter
`artifacts/evaluation/conversion_quality_review_v2/`.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0414_S.jpg` | Diff-Inventar | `0.31829609` | Sehr kompakte Kreis-/Innengeometrie mit hoher Abweichung. |
| 2 | `AC0130_M.jpg` | Diff-Inventar | `0.27991071` | Rechteck und Diagonalen sind als einfache bis mittlere Primitive abgrenzbar. |
| 3 | `AC0130.jpg` | Diff-Inventar | `0.23466992` | Größenverwandter Folgepunkt an der festgelegten Flächengrenze. |

Die Qualitätsnachmessung von `AC0922_S.jpg` korrigierte den veralteten Review-Wert `0.33015759` auf `0.02747206`. Der reale Re-Konvertierungsversuch wurde als semantische Regression verworfen, weil er Kreis und linken Anschluss durch ein Rechteck ersetzt hätte. Das bereits committete Kreis-/Anschluss-SVG bleibt deshalb die akzeptierte Ausgabe; die nächste Rotation beginnt mit `AC0414_S.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

Der aktualisierte Linkage-Report enthält die drei verbleibenden aktiven Kandidaten. Zwei
Perception-Fragen sind `generalisiert`: Kreis-/Ring-Signale für
`AC0414_S` und `AC0130`. `AC0130_M` ist `nur Sonderfall`, weil Rechteck und Diagonalen
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
