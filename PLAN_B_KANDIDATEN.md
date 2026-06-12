# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-12, Plan-B Run PC)

Das größenrelative AC0732-Geometry-IR wurde nun auch für die große Variante
`AC0732_1_L` real verifiziert. Linker Anschluss, roter Quadratgrundkörper und
horizontal bleibender P-Glyph bleiben getrennt; der reproduzierbare Review
entfernt die nun grüne Variante und nimmt `AC0845_S` als fünften Diff-Fall auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0254_2.jpg` | Diff-Inventar | `0.06059016` | Kompakte links gedrehte Klappenvariante mit Rechteckgrundkörper und drei Schließflächen. |
| 2 | `AC0732_1_S.jpg` | Diff-Inventar | `0.06000391` | Kleine nach rechts gedrehte Symbolvariante mit horizontal bleibendem P-Glyph. |
| 3 | `AC0701_1_S.jpg` | Diff-Inventar | `0.05935915` | Kleine aufrechte Quadrat-Kellen-Variante mit unterem Anschluss. |
| 4 | `AC0722_1_S.jpg` | Diff-Inventar | `0.05681223` | Kleine links gedrehte Quadrat-Kellen-Variante mit horizontal bleibendem T-Glyph. |
| 5 | `AC0845_S.jpg` | Diff-Inventar | `0.04927739` | Kleines kreisförmiges rH-Badge, dessen Alt-SVG fälschlich eine Außenleitung enthält. |

Die nächste reguläre Rotation beginnt mit `AC0254_2.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten.
`AC0254_2` bleibt `nur Sonderfall`, weil eine Linie, aber kein passender
allgemeiner Rechteck-/Rule-Seed erkannt wird. `AC0732_1_S`, `AC0701_1_S` und
`AC0722_1_S` bleiben `noch nicht erkannt`. Für `AC0845_S` erkennt PF8 dagegen
einen allgemeinen `CircleBackground`-Seed und entscheidet `generalisiert`; die
Text-Glyph-Erkennung bleibt Gegenstand des eigentlichen Plan-B-Pakets.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
