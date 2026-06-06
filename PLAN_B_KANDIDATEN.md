# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-06, nach AC0130-Run OL)

Die mit Run OG kuratierte Plan-B-/Perception-Rotation ist vollständig
abgearbeitet. Aktuell ist kein Kandidat aktiv; eine neue Rotation wird erst aus
einem reproduzierbaren Qualitätsrefresh abgeleitet.

`AC0130.jpg` wurde als dimensionstreues 40x80-Kühlelement mit Metallverlauf,
Außenrechteck, zwei beschnittenen Diagonalpfaden und zwei oberen Minuszeichen
rekonstruiert. Die Qualitätsmetrik sank von `0.23466992` auf `0.00985252`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

Die AC0130-Frage ist `generalisiert`: Außenlinien und Diagonalen werden als
Linien-/Rechteckkandidaten erkannt; die vorhandene Kreis-/Ring-Seed-Zuordnung
liefert zusätzlich einen vorinitialisierten Geometry-IR-Hinweis. Nach dem
Abschluss ist der aktive Linkage-Report synchron leer.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
