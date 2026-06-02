# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-02, nach AC0844-S-Refresh)

1. `AC0835_S.jpg` – Weak-Family-/QR-Befund: connector-freies rundes `VOC`-Badge mit knappem Review-Messwert (`normalized_mse=0.04467485`); gute Folgeprobe für Kreis und dreibuchstabiges Label.
2. `AC0861_S.jpg` – Weak-Family-Folgepunkt: rundes `rF`-Badge mit senkrechtem Griff unterhalb des Kreises; gute Probe für Kreis, zweibuchstabiges Label und unteren Connector.
3. `AC0862_S.jpg` – Weak-Family-Folgepunkt: rundes `rF`-Badge mit seitlichem Griff nach links; gute Probe für Kreis, zweibuchstabiges Label und horizontalen Connector.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

| Kandidat | Erste Perception-Frage | Erwartetes erstes Primitive | PF8-Entscheidung | Seed-Folge |
| --- | --- | --- | --- | --- |
| `AC0835_S.jpg` | Dominanten VOC-Kreis und dreibuchstabiges Label vorab festhalten? | `circle_ring_or_voc_label` | `generalisiert` | Kreis als `CircleBackground` seedbar; `VOC` bleibt ergänzende TextGlyph-Prüfung für Textgrösse und Grauwert. |
| `AC0861_S.jpg` | Dominanten rF-Kreis und unteren senkrechten Griff vorab festhalten? | `circle_ring_or_rf_vertical_connector` | `generalisiert` | Kreis als `CircleBackground` seedbar; `rF` und der senkrechte Griff bleiben gekoppelte TextGlyph-/Linien-Prüfung. |
| `AC0862_S.jpg` | Dominanten rF-Kreis und seitlichen Griff vorab festhalten? | `circle_ring_or_rf_horizontal_connector` | `generalisiert` | Kreis als `CircleBackground` seedbar; `rF` und der horizontale Griff bleiben gekoppelte TextGlyph-/Linien-Prüfung. |

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
