# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-05-31, nach AC0234-S-Refresh)

1. `AC0835_S.jpg` – Weak-Family-Befund: rundes `VOC`-Badge ohne Griff mit auffälligem Text-/Grauwertfehler (`normalized_mse=0.04467485`, knapp unter Review-Grenze, aber Priorität-A-Familie in der Vorprüfung).
2. `AC0820_S.jpg` – Weak-Family-Befund: rundes `CO2`-Badge mit tiefgestelltem Label; die Priorität-A-Familie bleibt wegen Text-/Grauwertfehlern eine geeignete nächste Nachzeichnungsprobe.
3. `AC0870_S.jpg` – Weak-Family-Befund: rundes `T`-Badge; einfache Grundform, aber Textgrösse, Zentrierung und Antialiasing sind weiterhin auffällig.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

| Kandidat | Erste Perception-Frage | Erwartetes erstes Primitive | PF8-Entscheidung | Seed-Folge |
| --- | --- | --- | --- | --- |
| `AC0835_S.jpg` | Dominanten VOC-Kreis und Label-Signal vorab festhalten? | `circle_ring_or_voc_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `VOC` bleibt ergänzende TextGlyph-Prüfung. |
| `AC0820_S.jpg` | Dominanten CO2-Kreis und kurzes Label vorab festhalten? | `circle_ring_or_co2_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `CO2` bleibt ergänzende TextGlyph-Prüfung für die tiefgestellte Ziffer. |
| `AC0870_S.jpg` | Dominanten T-Kreis und zentriertes Kurzlabel vorab festhalten? | `circle_ring_or_t_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `T` bleibt ergänzende TextGlyph-Prüfung für Zentrierung und Antialiasing. |

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
