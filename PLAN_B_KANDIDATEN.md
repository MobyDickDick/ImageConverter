# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-06, nach AC0130-M-Run OK)

Die Rotation wurde reproduzierbar aus dem aktualisierten Qualitätsreview erzeugt.
Priorisiert werden zuerst nicht zufriedenstellende Einträge aus
`successed_conversions.txt`, danach kompakte Varianten aus dem vorhandenen
Diff-Inventar. Die vollständige Evidenz liegt unter
`artifacts/evaluation/conversion_quality_review_v2/`.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0130.jpg` | Diff-Inventar | `0.23466992` | Größenverwandter Folgepunkt an der festgelegten Flächengrenze. |

`AC0130_M.jpg` wurde als dimensionstreuer Metallverlauf mit den im Referenzbild sichtbaren vertikalen Partitionen rekonstruiert. Die Qualitätsmetrik sank von `0.27991071` auf `0.00153867`; die beschriebene Diagonalgeometrie ist im realen JPG nicht stabil sichtbar und wurde deshalb nicht gegen die Bildtopologie erzwungen. Die nächste Rotation beginnt mit `AC0130.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

Der aktualisierte Linkage-Report enthält den letzten aktiven Kandidaten `AC0130`.
Seine Kreis-/Ring-Signale sind `generalisiert`; die AC0130-M-Frage bleibt als
abgeschlossener Sonderfall dokumentiert, weil der allgemeine Rechteck-Seed fehlt
und das reale JPG vertikale Partitionen statt stabiler Diagonalen zeigt.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
