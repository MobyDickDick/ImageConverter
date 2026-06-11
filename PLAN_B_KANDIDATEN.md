# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-11, Plan-B Run PA)

Das neue beschreibungsgetriebene AC0723-Geometry-IR trennt oberen Anschluss,
roten Quadratgrundkörper und horizontal bleibenden T-Glyph. Der reproduzierbare
Review entfernt `AC0723_1_S` und füllt die Rotation mit der kleinen aufrechten
AC0701-Variante wieder auf fünf Diff-Fälle auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0732_1_M.jpg` | Diff-Inventar | `0.06993533` | Mittlere nach rechts gedrehte Symbolvariante mit horizontal bleibendem P-Glyph. |
| 2 | `AC0732_1_L.jpg` | Diff-Inventar | `0.06552955` | Große nach rechts gedrehte Symbolvariante zur Prüfung von Grundgeometrie und horizontalem P-Glyph. |
| 3 | `AC0254_2.jpg` | Diff-Inventar | `0.06059016` | Kompakte links gedrehte Klappenvariante mit Rechteckgrundkörper und drei Schließflächen. |
| 4 | `AC0732_1_S.jpg` | Diff-Inventar | `0.06000391` | Kleine nach rechts gedrehte Symbolvariante mit horizontal bleibendem P-Glyph. |
| 5 | `AC0701_1_S.jpg` | Diff-Inventar | `0.05935915` | Kleine aufrechte Quadrat-Kellen-Variante mit unterem Anschluss. |

Die nächste reguläre Rotation beginnt mit `AC0732_1_M.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten.
`AC0254_2` bleibt `nur Sonderfall`, weil eine Linie, aber kein passender
allgemeiner Rechteck-/Rule-Seed erkannt wird. Alle drei AC0732-Größen werden
weiterhin von einer Kreisdetektion überlagert; `AC0701_1_S` liefert aktuell
keinen passenden Rechteck-/Linienkandidaten. Diese vier Fälle sind daher `noch
nicht erkannt`. Das AC0723-Beschreibungs-Geometry-IR ist als größenrelativer
Anschluss-/Quadrat-/T-Pfad umgesetzt; die vorgelagerte PF8-Erkennung bleibt ein
separater allgemeiner Folgeschritt.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
