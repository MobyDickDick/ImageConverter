# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-05-31, nach AC0835-S-Refresh)

1. `AC0820_S.jpg` – Weak-Family-Befund: rundes `CO2`-Badge mit tiefgestelltem Label; die Priorität-A-Familie bleibt wegen Text-/Grauwertfehlern eine geeignete nächste Nachzeichnungsprobe.
2. `AC0870_S.jpg` – Weak-Family-Befund: rundes `T`-Badge; einfache Grundform, aber Textgrösse, Zentrierung und Antialiasing sind weiterhin auffällig.
3. `AC0850_M.jpg` – Weak-Family-Befund: rundes `rF`-Badge ohne Griff mit sehr hohem Text-/Grauwertfehler (`mean_delta2=13599.945312` in der AC08-Weak-Family-Rangliste).

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

| Kandidat | Erste Perception-Frage | Erwartetes erstes Primitive | PF8-Entscheidung | Seed-Folge |
| --- | --- | --- | --- | --- |
| `AC0820_S.jpg` | Dominanten CO2-Kreis und kurzes Label vorab festhalten? | `circle_ring_or_co2_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `CO2` bleibt ergänzende TextGlyph-Prüfung für die tiefgestellte Ziffer. |
| `AC0870_S.jpg` | Dominanten T-Kreis und zentriertes Kurzlabel vorab festhalten? | `circle_ring_or_t_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `T` bleibt ergänzende TextGlyph-Prüfung für Zentrierung und Antialiasing. |
| `AC0850_M.jpg` | Dominanten rF-Kreis und zweibuchstabiges Label vorab festhalten? | `circle_ring_or_rf_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `rF` bleibt ergänzende TextGlyph-Prüfung für Textgrösse und Grauwert. |

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
