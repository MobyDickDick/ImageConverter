# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-11, Plan-B Run OZ)

Das neue beschreibungsgetriebene AC0722-Geometry-IR trennt horizontalen
Anschluss, roten Quadratgrundkörper und horizontal bleibenden T-Glyph. Der
reproduzierbare Review entfernt `AC0722_1_L` und füllt die Rotation mit der
kleinen AC0732-Variante wieder auf fünf Diff-Fälle auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0723_1_S.jpg` | Diff-Inventar | `0.07402805` | Kleine vertikal gespiegelte Kellen-Variante mit quadratischem Grundkörper und Anschluss. |
| 2 | `AC0732_1_M.jpg` | Diff-Inventar | `0.06993533` | Mittlere nach rechts gedrehte Symbolvariante mit horizontal bleibendem P-Glyph. |
| 3 | `AC0732_1_L.jpg` | Diff-Inventar | `0.06552955` | Große nach rechts gedrehte Symbolvariante zur Prüfung von Grundgeometrie und horizontalem P-Glyph. |
| 4 | `AC0254_2.jpg` | Diff-Inventar | `0.06059016` | Kompakte links gedrehte Klappenvariante mit Rechteckgrundkörper und drei Schließflächen. |
| 5 | `AC0732_1_S.jpg` | Diff-Inventar | `0.06000391` | Kleine nach rechts gedrehte Symbolvariante mit horizontal bleibendem P-Glyph. |

Die nächste reguläre Rotation beginnt mit `AC0723_1_S.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten.
`AC0723_1_S` und `AC0254_2` bleiben `nur Sonderfall`, weil jeweils eine Linie,
aber kein passender allgemeiner Rechteck-/Rule-Seed erkannt wird. Alle drei
AC0732-Größen sind wegen einer fälschlich priorisierten Kreisdetektion `noch
nicht erkannt`. Das AC0722-Beschreibungs-Geometry-IR ist dagegen als
größenrelativer Anschluss-/Quadrat-/T-Pfad umgesetzt; die vorgelagerte PF8-
Erkennung bleibt ein separater allgemeiner Folgeschritt.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
