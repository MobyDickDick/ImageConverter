# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-12, Plan-B Run PD)

`AC0254_2` wurde nach Sichtprüfung nicht als Rechteckklappe, sondern als grüner
Kreisgrundkörper mit links zeigendem hellem Schließblatt rekonstruiert. Das neue
beschreibungsgetriebene Geometry-IR hält Kreis und Blatt als getrennte Primitive;
der reproduzierbare Review entfernt die nun grüne Variante. Der qualifizierte
Diff-Pool enthält aktuell nur vier weitere Fälle oberhalb der Review-Grenze.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0732_1_S.jpg` | Diff-Inventar | `0.06000391` | Kleine nach rechts gedrehte Symbolvariante mit horizontal bleibendem P-Glyph. |
| 2 | `AC0701_1_S.jpg` | Diff-Inventar | `0.05935915` | Kleine aufrechte Quadrat-Kellen-Variante mit unterem Anschluss. |
| 3 | `AC0722_1_S.jpg` | Diff-Inventar | `0.05681223` | Kleine links gedrehte Quadrat-Kellen-Variante mit horizontal bleibendem T-Glyph. |
| 4 | `AC0845_S.jpg` | Diff-Inventar | `0.04927739` | Kleines kreisförmiges rH-Badge, dessen Alt-SVG fälschlich eine Außenleitung enthält. |

Die nächste reguläre Rotation beginnt mit `AC0732_1_S.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält alle vier aktiven Kandidaten.
`AC0732_1_S`, `AC0701_1_S` und `AC0722_1_S` bleiben `noch nicht erkannt`.
Für `AC0845_S` erkennt PF8 dagegen einen allgemeinen `CircleBackground`-Seed
und entscheidet `generalisiert`; die Text-Glyph-Erkennung bleibt Gegenstand des
eigentlichen Plan-B-Pakets. Bei `AC0254_2` hatte die frühere Rechteckannahme nur
eine Hough-Linie geliefert. Die reale Rekonstruktion korrigiert die Topologie
auf Kreis plus dreieckiges Schließblatt, ohne daraus einen unzutreffenden
allgemeinen Rechteck-Seed abzuleiten.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
