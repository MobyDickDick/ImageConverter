# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-11, Plan-B Run OW)

Die reale AC0551-2-M-Re-Konvertierung bestätigt, dass die bereits für die erste
Familienvariante eingeführte beschreibungsgetriebene Chevron-Topologie ohne
variantenspezifische Koordinaten generalisiert. Der reproduzierbare Review
entfernt den abgeschlossenen Kandidaten und füllt die Rotation mit
`AC0732_1_M` wieder auf fünf Diff-Fälle auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0733_1_L.jpg` | Diff-Inventar | `0.09223704` | Kompaktes gedrehtes Symbol, dessen P-Glyph laut Beschreibung horizontal bleiben muss. |
| 2 | `AC0733_1_M.jpg` | Diff-Inventar | `0.08842208` | Mittlere Variante desselben gedrehten Symbols zur Prüfung der P-Glyph-Generalisierung. |
| 3 | `AC0722_1_L.jpg` | Diff-Inventar | `0.07686921` | Kompaktes links gedrehtes Kellen-Symbol mit Anschluss, rotem Quadrat und T-Glyph. |
| 4 | `AC0723_1_S.jpg` | Diff-Inventar | `0.07402805` | Kleine vertikal gespiegelte Kellen-Variante mit quadratischem Grundkörper und Anschluss. |
| 5 | `AC0732_1_M.jpg` | Diff-Inventar | `0.06993533` | Mittlere nach rechts gedrehte Symbolvariante mit horizontal bleibendem P-Glyph. |

Die nächste reguläre Rotation beginnt mit `AC0733_1_L.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten.
`AC0733_1_L`, `AC0733_1_M` und `AC0723_1_S` bleiben `nur Sonderfall`, solange
ihre Linien- oder Textprimitive keinen passenden allgemeinen Seed liefern.
`AC0722_1_L` und der neu rotierte Kandidat `AC0732_1_M` sind wegen einer
fälschlich priorisierten Kreisdetektion `noch nicht erkannt`. Die
Chevron-Rekonstruktion von `AC0551_2_M` ist durch den realen Lauf als
allgemeiner Familienpfad bestätigt.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
