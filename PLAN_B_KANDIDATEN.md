# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-12, Plan-B Run PB)

Das neue beschreibungsgetriebene AC0732-Geometry-IR toleriert den Schreibfehler
`gredreht`, trennt linken Anschluss, roten Quadratgrundkörper und horizontal
bleibenden P-Glyph und entfernt `AC0732_1_M` aus der Rotation. Der
reproduzierbare Review nimmt `AC0722_1_S` als fünften Diff-Fall auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0732_1_L.jpg` | Diff-Inventar | `0.06552955` | Große nach rechts gedrehte Symbolvariante zur Prüfung von Grundgeometrie und horizontalem P-Glyph. |
| 2 | `AC0254_2.jpg` | Diff-Inventar | `0.06059016` | Kompakte links gedrehte Klappenvariante mit Rechteckgrundkörper und drei Schließflächen. |
| 3 | `AC0732_1_S.jpg` | Diff-Inventar | `0.06000391` | Kleine nach rechts gedrehte Symbolvariante mit horizontal bleibendem P-Glyph. |
| 4 | `AC0701_1_S.jpg` | Diff-Inventar | `0.05935915` | Kleine aufrechte Quadrat-Kellen-Variante mit unterem Anschluss. |
| 5 | `AC0722_1_S.jpg` | Diff-Inventar | `0.05681223` | Kleine links gedrehte Quadrat-Kellen-Variante mit horizontal bleibendem T-Glyph. |

Die nächste reguläre Rotation beginnt mit `AC0732_1_L.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten.
`AC0254_2` bleibt `nur Sonderfall`, weil eine Linie, aber kein passender
allgemeiner Rechteck-/Rule-Seed erkannt wird. `AC0732_1_L`, `AC0732_1_S`,
`AC0701_1_S` und `AC0722_1_S` liefern noch keine vollständige allgemeine
Rechteck-/Linien-/Text-Erkennung und bleiben `noch nicht erkannt`. Das
AC0732-Beschreibungs-Geometry-IR ist davon getrennt als größenrelativer
Anschluss-/Quadrat-/P-Pfad generalisiert.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
