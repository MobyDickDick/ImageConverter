# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-08, Plan-B Run OP)

Die reale AC0820-L-Re-Konvertierung hat den einzigen roten Eintrag aus der
Erfolgsliste unter die Review-Grenze gebracht. Der reproduzierbare Review füllt
die Rotation anschließend wieder auf maximal fünf kompakte Diff-Fälle auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0531_1_S.jpg` | Diff-Inventar | `0.15610678` | Höchste verbleibende Abweichung unter den kompakten renderbaren Fällen; Rechteck, Diagonale und Mittelpunkt sind klar abgrenzbar. |
| 2 | `AC0502_1_M.jpg` | Diff-Inventar | `0.15533278` | Gedrehte Klappengeometrie mit sehr hoher Abweichung und wiederverwendbaren Rechteck-/Punkt-Primitiven. |
| 3 | `AC0551_1_M.jpg` | Diff-Inventar | `0.14916385` | Kompaktes Rechteckmotiv mit horizontalen Teilungen und mittiger Winkelkontur. |
| 4 | `AC0403_1_M.jpg` | Diff-Inventar | `0.11117438` | Sehr kompakte gedrehte Kreis-/Innengeometrie oberhalb der Review-Grenze. |
| 5 | `AC0150_2.jpg` | Diff-Inventar | `0.10493784` | Dimensionstreues Rechteck-/Linienmotiv an der maximal zulässigen kompakten Bildfläche. |

Die nächste reguläre Rotation beginnt mit `AC0531_1_S.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten. Drei
Fragen sind `generalisiert`: Kreis-/Ring-Erkennung für `AC0403_1_M` sowie
allgemeine Primitive und ein Kreis-Seed für die beiden Klappenvarianten
`AC0531_1_S` und `AC0502_1_M`. `AC0551_1_M` und `AC0150_2` bleiben
`nur Sonderfall`, weil Linien und Rechteck erkannt werden, aber weder ein
allgemeiner Rechteck- noch HorizontalRule-Seed vorliegt. Der Kreis-/CO₂-
Lerneffekt von `AC0820_L` ist mit dem realen Lauf abgeschlossen.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
