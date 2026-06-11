# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-11, Plan-B Run OY)

Die mittlere AC0733-1-Variante bestätigt das im vorherigen Paket eingeführte
beschreibungsgetriebene Quadrat-Kellen-Geometry-IR ohne neue Sonderfalllogik.
Der reproduzierbare Review entfernt `AC0733_1_M` und füllt die Rotation mit
`AC0254_2` wieder auf fünf Diff-Fälle auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0722_1_L.jpg` | Diff-Inventar | `0.07686921` | Kompaktes links gedrehtes Kellen-Symbol mit Anschluss, rotem Quadrat und T-Glyph. |
| 2 | `AC0723_1_S.jpg` | Diff-Inventar | `0.07402805` | Kleine vertikal gespiegelte Kellen-Variante mit quadratischem Grundkörper und Anschluss. |
| 3 | `AC0732_1_M.jpg` | Diff-Inventar | `0.06993533` | Mittlere nach rechts gedrehte Symbolvariante mit horizontal bleibendem P-Glyph. |
| 4 | `AC0732_1_L.jpg` | Diff-Inventar | `0.06552955` | Große nach rechts gedrehte Symbolvariante zur Prüfung von Grundgeometrie und horizontalem P-Glyph. |
| 5 | `AC0254_2.jpg` | Diff-Inventar | `0.06059016` | Kompakte links gedrehte Klappenvariante mit Rechteckgrundkörper und drei Schließflächen. |

Die nächste reguläre Rotation beginnt mit `AC0722_1_L.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten.
`AC0723_1_S` und `AC0254_2` bleiben `nur Sonderfall`, weil jeweils eine Linie,
aber kein passender allgemeiner Rechteck-/Rule-Seed erkannt wird. `AC0722_1_L`,
`AC0732_1_M` und `AC0732_1_L` sind wegen einer fälschlich priorisierten
Kreisdetektion `noch nicht erkannt`. Das AC0733-Geometry-IR ist durch zwei
reale Größenvarianten als größenrelativer Familienpfad bestätigt.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
