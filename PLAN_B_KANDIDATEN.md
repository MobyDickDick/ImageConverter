# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-05-31, nach AC0820-S-Refresh)

1. `AC0870_S.jpg` – Weak-Family-Befund: rundes `T`-Badge; einfache Grundform, aber Textgrösse, Zentrierung und Antialiasing sind weiterhin auffällig.
2. `AC0850_M.jpg` – Weak-Family-Befund: rundes `rF`-Badge ohne Griff mit sehr hohem Text-/Grauwertfehler (`mean_delta2=13599.945312` in der AC08-Weak-Family-Rangliste).
3. `AC0836_S.jpg` – Weak-Family-Befund: rundes `VOC`-Badge mit senkrechtem Griff; gute nächste Probe für Kreis, Label und einfachen Connector.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

| Kandidat | Erste Perception-Frage | Erwartetes erstes Primitive | PF8-Entscheidung | Seed-Folge |
| --- | --- | --- | --- | --- |
| `AC0870_S.jpg` | Dominanten T-Kreis und zentriertes Kurzlabel vorab festhalten? | `circle_ring_or_t_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `T` bleibt ergänzende TextGlyph-Prüfung für Zentrierung und Antialiasing. |
| `AC0850_M.jpg` | Dominanten rF-Kreis und zweibuchstabiges Label vorab festhalten? | `circle_ring_or_rf_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `rF` bleibt ergänzende TextGlyph-Prüfung für Textgrösse und Grauwert. |
| `AC0836_S.jpg` | Dominanten VOC-Kreis und senkrechten Griff vorab festhalten? | `circle_ring_or_vertical_connector` | `generalisiert` | Kreis als `CircleBackground` seedbar; `VOC` und der Griff bleiben gekoppelte TextGlyph-/Linien-Prüfung. |

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
