# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-05-31, nach AC0838-M-Plan-B-Review)

1. `AC0881_M.jpg` – Qualitätsreview-Befund: Originalbild vorhanden, aber kein passendes SVG-Artefakt in den geprüften Konvertierungs-/Baseline-Pfaden.
2. `AC0234_S.jpg` – AC0231-verwandtes 3-Wege-Ventil, hauptdiagonal gespiegelt und mit vorhandenem Diff-Artefakt.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

| Kandidat | Erste Perception-Frage | Erwartetes erstes Primitive | PF8-Entscheidung | Seed-Folge |
| --- | --- | --- | --- | --- |
| `AC0881_M.jpg` | Einfaches Rahmen-, Kreis- oder Linienprimitive zuerst erkennen? | `simple_shape_probe` | `generalisiert` | Gefundene Kreis-/HorizontalRule-Signale als Startseed prüfen. |
| `AC0234_S.jpg` | Gespiegelte Kelle mit Kreis- und `M`-Signal vor der ersten Iteration erkennen? | `text_glyph_or_circle_ring` | `generalisiert` | Kreis als `CircleBackground` seedbar; `M` bleibt ergänzender Label-Hinweis für die gespiegelte AC0231-Folgeform. |

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
