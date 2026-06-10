# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-09, Plan-B Run OU)

Die reale AC0150-2-Re-Konvertierung nutzt nun die bereits allgemeine
beschreibungsgetriebene Chevron-Topologie zusammen mit einer robusten,
rahmenunempfindlichen RGB-Farbmessung. Der reproduzierbare Review entfernt
den abgeschlossenen Kandidaten und füllt die Rotation mit `AC0722_1_L` wieder
auf fünf Diff-Fälle auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0253_1.jpg` | Diff-Inventar | `0.10473690` | Kompaktes um 180° gedrehtes Pumpensymbol; Außenkreis und inneres Dreieck sind klar getrennt prüfbar. |
| 2 | `AC0551_2_M.jpg` | Diff-Inventar | `0.09445446` | Zweite kompakte Rechteck-/Linienvariante derselben Familie zur Prüfung der Generalisierung. |
| 3 | `AC0733_1_L.jpg` | Diff-Inventar | `0.09223704` | Kompaktes gedrehtes Symbol, dessen P-Glyph laut Beschreibung horizontal bleiben muss. |
| 4 | `AC0733_1_M.jpg` | Diff-Inventar | `0.08842208` | Mittlere Variante desselben gedrehten Symbols zur Prüfung der P-Glyph-Generalisierung. |
| 5 | `AC0722_1_L.jpg` | Diff-Inventar | `0.07686921` | Kompaktes links gedrehtes Kellen-Symbol mit Anschluss, rotem Quadrat und T-Glyph. |

Die nächste reguläre Rotation beginnt mit `AC0253_1.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jeder aktive Kandidat ist mit einer expliziten Perception-Frage, erwarteten
Primitiven und einer Entscheidung `generalisiert`, `nur Sonderfall` oder
`noch nicht erkannt` gekoppelt. Der maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten. Die
Kreis-/Dreieck-Frage für `AC0253_1` ist `generalisiert`; `AC0551_2_M`,
`AC0733_1_L` und `AC0733_1_M` bleiben `nur Sonderfall`. Der neu rotierte
Kandidat `AC0722_1_L` ist wegen der fälschlich priorisierten Kreisdetektion
`noch nicht erkannt`. Die Chevron-Rekonstruktion von `AC0150_2` ist mit dem
realen Lauf abgeschlossen; die zentrale Farbmessung bleibt allgemein und
enthält keine variantenspezifischen Koordinaten.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
