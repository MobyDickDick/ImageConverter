# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-11, Plan-B Run OV)

Die reale AC0253-1-Re-Konvertierung bestätigt die allgemeine Übertragbarkeit
des beschreibungsgetriebenen Pumpen-Geometry-IR auf die AC0251-Familie. Der
reproduzierbare Review entfernt den abgeschlossenen Kandidaten und füllt die
Rotation mit `AC0723_1_S` wieder auf fünf Diff-Fälle auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0551_2_M.jpg` | Diff-Inventar | `0.09445446` | Zweite kompakte Rechteck-/Linienvariante derselben Familie zur Prüfung der Generalisierung. |
| 2 | `AC0733_1_L.jpg` | Diff-Inventar | `0.09223704` | Kompaktes gedrehtes Symbol, dessen P-Glyph laut Beschreibung horizontal bleiben muss. |
| 3 | `AC0733_1_M.jpg` | Diff-Inventar | `0.08842208` | Mittlere Variante desselben gedrehten Symbols zur Prüfung der P-Glyph-Generalisierung. |
| 4 | `AC0722_1_L.jpg` | Diff-Inventar | `0.07686921` | Kompaktes links gedrehtes Kellen-Symbol mit Anschluss, rotem Quadrat und T-Glyph. |
| 5 | `AC0723_1_S.jpg` | Diff-Inventar | `0.07402805` | Kleine vertikal gespiegelte Kellen-Variante mit quadratischem Grundkörper und Anschluss. |

Die nächste reguläre Rotation beginnt mit `AC0551_2_M.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten.
`AC0551_2_M`, `AC0733_1_L`, `AC0733_1_M` und der neu rotierte Kandidat
`AC0723_1_S` bleiben `nur Sonderfall`, solange ihre Rechteck-, Linien- oder
Textprimitive keinen passenden allgemeinen Seed liefern. `AC0722_1_L` ist
wegen der fälschlich priorisierten Kreisdetektion weiterhin `noch nicht
erkannt`. Die Kreis-/Dreieck-Rekonstruktion von `AC0253_1` ist durch den
realen Lauf als allgemeiner Familienpfad bestätigt.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
