# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-12, Plan-B Run PE)

Das gemeinsame, größenrelative AC0732-Geometry-IR wurde nun auch für die kleine
Variante `AC0732_1_S` real verifiziert. Linker Anschluss, roter
Quadratgrundkörper und horizontal bleibender P-Glyph bleiben getrennte
Vektorelemente; der reproduzierbare Review entfernt die nun grüne Variante.
Der qualifizierte Diff-Pool enthält aktuell nur noch drei Fälle oberhalb der
Review-Grenze.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0701_1_S.jpg` | Diff-Inventar | `0.05935915` | Kleine aufrechte Quadrat-Kellen-Variante mit unterem Anschluss. |
| 2 | `AC0722_1_S.jpg` | Diff-Inventar | `0.05681223` | Kleine links gedrehte Quadrat-Kellen-Variante mit horizontal bleibendem T-Glyph. |
| 3 | `AC0845_S.jpg` | Diff-Inventar | `0.04927739` | Kleines kreisförmiges rH-Badge, dessen Alt-SVG fälschlich eine Außenleitung enthält. |

Die nächste reguläre Rotation beginnt mit `AC0701_1_S.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält alle drei aktiven Kandidaten.
`AC0701_1_S` und `AC0722_1_S` bleiben `noch nicht erkannt`. Für `AC0845_S`
erkennt PF8 dagegen einen allgemeinen `CircleBackground`-Seed und entscheidet
`generalisiert`; die Text-Glyph-Erkennung bleibt Gegenstand des eigentlichen
Plan-B-Pakets. `AC0732_1_S` ist nicht mehr aktiv: Die reale Konvertierung
bestätigt den bereits für L und M eingeführten allgemeinen AC0732-Pfad, ohne
einen unvollständigen PF8-Rechteck-/Text-Seed als Voraussetzung auszugeben.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
