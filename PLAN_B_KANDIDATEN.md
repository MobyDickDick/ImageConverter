# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-09, Plan-B Run OS)

Die reale AC0551-1-M-Re-Konvertierung rekonstruiert die beschriebene rechte
Winkelkontur nun als allgemeine, rasterangepasste Polylinie. Der
reproduzierbare Review entfernt den abgeschlossenen Kandidaten und füllt die
Rotation mit dem kompakten gedrehten P-Symbol `AC0733_1_L` wieder auf maximal
fünf Diff-Fälle auf.

| Priorität | Kandidat | Quelle | `normalized_mse` | Auswahlgrund |
| ---: | --- | --- | ---: | --- |
| 1 | `AC0403_1_M.jpg` | Diff-Inventar | `0.11117438` | Sehr kompakte gedrehte Kreis-/Innengeometrie oberhalb der Review-Grenze. |
| 2 | `AC0150_2.jpg` | Diff-Inventar | `0.10493784` | Dimensionstreues Rechteck-/Linienmotiv an der maximal zulässigen kompakten Bildfläche. |
| 3 | `AC0253_1.jpg` | Diff-Inventar | `0.10473690` | Kompaktes um 180° gedrehtes Pumpensymbol; Außenkreis und inneres Dreieck sind klar getrennt prüfbar. |
| 4 | `AC0551_2_M.jpg` | Diff-Inventar | `0.09445446` | Zweite kompakte Rechteck-/Linienvariante derselben Familie zur Prüfung der Generalisierung. |
| 5 | `AC0733_1_L.jpg` | Diff-Inventar | `0.09223704` | Kompaktes gedrehtes Symbol, dessen P-Glyph laut Beschreibung horizontal bleiben muss. |

Die nächste reguläre Rotation beginnt mit `AC0403_1_M.jpg`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Jedes kommende Plan-B-Arbeitspaket übernimmt genau eine Perception-Frage aus
dem PF8-Linkage-Report und dokumentiert die Entscheidung als
`generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`. Der aktuelle
maschinenlesbare Stand liegt unter
`artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json`.

Der aktualisierte Linkage-Report enthält alle fünf aktiven Kandidaten. Die
Kreis-/Ring-Fragen für `AC0403_1_M` und `AC0253_1` sind `generalisiert`.
`AC0150_2`, `AC0551_2_M` und `AC0733_1_L` bleiben `nur Sonderfall`, weil ihre
Linien-/Rechteck- beziehungsweise Textprimitive noch keinen passenden
allgemeinen Seed liefern. Der Beschreibungs- und Raster-Fit der rechten
Winkelkontur von `AC0551_1_M` ist mit dem realen Lauf abgeschlossen.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
