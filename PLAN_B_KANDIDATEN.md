# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-08, Plan-B Run OQ)

Die reale AC0531-1-S-Re-Konvertierung hat Rechteck, einzelne Diagonale,
Mittelpunkt und den rastergemessenen Farbverlauf algorithmisch rekonstruiert.
Der reproduzierbare Review entfernt den abgeschlossenen Kandidaten und füllt
die Rotation wieder auf maximal fünf kompakte Diff-Fälle auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0502_1_M.jpg` | Diff-Inventar | `0.15533278` | Gedrehte Klappengeometrie mit sehr hoher Abweichung und wiederverwendbaren Rechteck-/Punkt-Primitiven. |
| 2 | `AC0551_1_M.jpg` | Diff-Inventar | `0.14916385` | Kompaktes Rechteckmotiv mit horizontalen Teilungen und mittiger Winkelkontur. |
| 3 | `AC0403_1_M.jpg` | Diff-Inventar | `0.11117438` | Sehr kompakte gedrehte Kreis-/Innengeometrie oberhalb der Review-Grenze. |
| 4 | `AC0150_2.jpg` | Diff-Inventar | `0.10493784` | Dimensionstreues Rechteck-/Linienmotiv an der maximal zulässigen kompakten Bildfläche. |
| 5 | `AC0253_1.jpg` | Diff-Inventar | `0.10473690` | Kompaktes um 180° gedrehtes Pumpensymbol; Außenkreis und inneres Dreieck sind klar getrennt prüfbar. |

Die nächste reguläre Rotation beginnt mit `AC0502_1_M.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten. Drei
Fragen sind `generalisiert`: Kreis-/Ring-Erkennung für `AC0403_1_M` und
`AC0253_1` sowie allgemeine Primitive mit Kreis-Seed für `AC0502_1_M`.
`AC0551_1_M` und `AC0150_2` bleiben `nur Sonderfall`, weil Linien und
Rechteck erkannt werden, aber weder ein allgemeiner Rechteck- noch
HorizontalRule-Seed vorliegt. Der Rechteck-/Diagonal-/Mittelpunkt-Lerneffekt
von `AC0531_1_S` ist mit dem realen Lauf abgeschlossen.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
