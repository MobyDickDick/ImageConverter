# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-04, nach AC0861-S-Run)

1. `AC0862_S.jpg` – Weak-Family-Folgepunkt: rundes `rF`-Badge mit seitlichem Griff nach links; gute Probe für Kreis, zweibuchstabiges Label und horizontalen Connector.
2. `AC0863_S.jpg` – Weak-Family-Folgepunkt: gedrehtes `rF`-Badge nach AC0842 mit horizontal bleibendem Text; gute Probe für Kreis, zweibuchstabiges Label und gedrehten Connector.
3. `AC0864_S.jpg` – Weak-Family-Folgepunkt: horizontal gespiegeltes gedrehtes `rF`-Badge nach AC0862; gute Probe für Kreis, zweibuchstabiges Label und gespiegelten Connector.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

| Kandidat | Erste Perception-Frage | Erwartetes erstes Primitive | PF8-Entscheidung | Seed-Folge |
| --- | --- | --- | --- | --- |
| `AC0862_S.jpg` | Dominanten rF-Kreis und seitlichen Griff vorab festhalten? | `circle_ring_or_rf_horizontal_connector` | `generalisiert` | Kreis als `CircleBackground` seedbar; `rF` und der horizontale Griff bleiben gekoppelte TextGlyph-/Linien-Prüfung. |
| `AC0863_S.jpg` | Dominanten rF-Kreis und gedrehten Connector vorab festhalten? | `circle_ring_or_rf_rotated_connector` | `generalisiert` | Kreis als `CircleBackground` seedbar; `rF` und der gedrehte Connector bleiben gekoppelte TextGlyph-/Linien-Prüfung. |
| `AC0864_S.jpg` | Dominanten rF-Kreis und gespiegelten Connector vorab festhalten? | `circle_ring_or_rf_mirrored_connector` | `generalisiert` | Kreis als `CircleBackground` seedbar; `rF` und der gespiegelte Connector bleiben gekoppelte TextGlyph-/Linien-Prüfung. |

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
