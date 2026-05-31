# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-05-31, nach AC0850-M-Refresh)

1. `AC0836_S.jpg` – Weak-Family-Befund: rundes `VOC`-Badge mit senkrechtem Griff; gute nächste Probe für Kreis, Label und einfachen Connector.
2. `AC0835_S.jpg` – Weak-Family-Befund: rundes `VOC`-Badge ohne Griff; Priorität-A-Familie für reine Kreis-/Label-Zentrierung.
3. `AC0861_S.jpg` – Anschlussprobe aus der rF-Familie: rundes `rF`-Badge mit senkrechtem Griff; prüft, ob der AC0850-Lerneffekt auf Connector-Badges übertragbar bleibt.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

| Kandidat | Erste Perception-Frage | Erwartetes erstes Primitive | PF8-Entscheidung | Seed-Folge |
| --- | --- | --- | --- | --- |
| `AC0836_S.jpg` | Dominanten VOC-Kreis und senkrechten Griff vorab festhalten? | `circle_ring_or_vertical_connector` | `generalisiert` | Kreis als `CircleBackground` seedbar; `VOC` und der Griff bleiben gekoppelte TextGlyph-/Linien-Prüfung. |
| `AC0835_S.jpg` | Dominanten VOC-Kreis und dreibuchstabiges Label vorab festhalten? | `circle_ring_or_voc_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `VOC` bleibt ergänzende TextGlyph-Prüfung für reine Kreis-/Label-Zentrierung. |
| `AC0861_S.jpg` | Dominanten rF-Kreis und senkrechten Griff gemeinsam vorab festhalten? | `circle_ring_or_rf_vertical_connector` | `generalisiert` | Kreis als `CircleBackground` seedbar; `rF` und Griff bleiben gekoppelte TextGlyph-/Linien-Prüfung nach dem AC0850-Refresh. |

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
