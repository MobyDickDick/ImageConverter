# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-05-31, nach AC0224-S-Plan-B-Rotation)

1. `AC0231_S.jpg` – AC0221-verwandtes 3-Wege-Ventil mit oberer `M`-Kelle und vorhandenem Diff-Artefakt.
2. `AC0232_S.jpg` – AC0231-verwandtes 3-Wege-Ventil, 90° nach links gedreht und mit vorhandenem Diff-Artefakt.
3. `AC0838_M.jpg` – Qualitätsreview-Befund: vorhandenes SVG-Paar rendert, überschreitet aber die Review-Grenze (`normalized_mse=0.04729276`).
4. `AC0881_M.jpg` – Qualitätsreview-Befund: Originalbild vorhanden, aber kein passendes SVG-Artefakt in den geprüften Konvertierungs-/Baseline-Pfaden.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

| Kandidat | Erste Perception-Frage | Erwartetes erstes Primitive | PF8-Entscheidung | Seed-Folge |
| --- | --- | --- | --- | --- |
| `AC0231_S.jpg` | Obere `M`-Kelle über Label- oder Kreis-Signal absichern? | `text_glyph_or_circle_ring` | `generalisiert` | Kreis zunächst als `CircleBackground` seedbar; `M` zusätzlich als Label-Hinweis dokumentieren. |
| `AC0232_S.jpg` | Gedrehte Kelle mit Kreis- und `M`-Signal vor der ersten Iteration erkennen? | `text_glyph_or_circle_ring` | `generalisiert` | Kreis als `CircleBackground` seedbar; `M` bleibt ergänzender Label-Hinweis wie bei `AC0231_S`. |
| `AC0838_M.jpg` | Dominanten VOC-Kreis und Label-Signal vorab festhalten? | `circle_ring_or_voc_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `VOC` bleibt ergänzende TextGlyph-Prüfung. |
| `AC0881_M.jpg` | Einfaches Rahmen-, Kreis- oder Linienprimitive zuerst erkennen? | `simple_shape_probe` | `generalisiert` | Gefundene Kreis-/HorizontalRule-Signale als Startseed prüfen. |

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
