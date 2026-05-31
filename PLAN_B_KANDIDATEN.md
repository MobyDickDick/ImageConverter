# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-05-31, nach AC0881-M-Qualitätsrefresh)

1. `AC0234_S.jpg` – AC0231-verwandtes 3-Wege-Ventil, hauptdiagonal gespiegelt und mit vorhandenem Diff-Artefakt.
2. `AC0835_S.jpg` – Weak-Family-Befund: rundes `VOC`-Badge ohne Griff mit auffälligem Text-/Grauwertfehler (`normalized_mse=0.04467485`, knapp unter Review-Grenze, aber Priorität-A-Familie in der Vorprüfung).
3. `AC0820_S.jpg` – Weak-Family-Befund: rundes `CO2`-Badge mit tiefgestelltem Label; die Priorität-A-Familie bleibt wegen Text-/Grauwertfehlern eine geeignete nächste Nachzeichnungsprobe.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

| Kandidat | Erste Perception-Frage | Erwartetes erstes Primitive | PF8-Entscheidung | Seed-Folge |
| --- | --- | --- | --- | --- |
| `AC0234_S.jpg` | Gespiegelte Kelle mit Kreis- und `M`-Signal vor der ersten Iteration erkennen? | `text_glyph_or_circle_ring` | `generalisiert` | Kreis als `CircleBackground` seedbar; `M` bleibt ergänzender Label-Hinweis für die gespiegelte AC0231-Folgeform. |
| `AC0835_S.jpg` | Dominanten VOC-Kreis und Label-Signal vorab festhalten? | `circle_ring_or_voc_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `VOC` bleibt ergänzende TextGlyph-Prüfung. |
| `AC0820_S.jpg` | Dominanten CO2-Kreis und kurzes Label vorab festhalten? | `circle_ring_or_co2_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `CO2` bleibt ergänzende TextGlyph-Prüfung für die tiefgestellte Ziffer. |

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
