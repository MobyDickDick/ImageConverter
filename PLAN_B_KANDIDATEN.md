# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-21, Review-Refresh Run RQ)

Der reproduzierbare Review mit `tools/review_conversion_quality.py --max-candidates 5` findet aktuell zwei qualifizierte Diff-Fälle oberhalb der Review-Grenze. Die Reihenfolge folgt der automatisch erzeugten Triage `artifacts/evaluation/conversion_quality_review_v2/plan_b_candidate_triage_v1.csv`. Wichtig: Die Review-Grenze ist nur ein grobes technisches Gate; die harte Pixelnähe-Metrik `mean_delta2 <= 18.000` zeigt weiterhin, dass beide Diff-Paare sichtbar verbesserungsbedürftig sind.

1. `GE1001_M` – höchster aktueller `normalized_mse`-Fehler der kompakten Plan-B-Triage (`mean_delta2=18208.14453125`, `normalized_mse=0.09333920046776881`).
2. `GE9021_7M` – zweiter aktueller Diff-Fall oberhalb der Review-Grenze (`mean_delta2=9378.9921875`, `normalized_mse=0.0480789039471998`).

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Die Run-RQ-Triage verschiebt die aktive Rotation von der GE9002-Familie auf zwei kleinere GE-Diff-Fälle. Vor der konkreten Nachzeichnung ist für `GE1001_M` zu prüfen, ob die dominanten grafischen Primitive bereits als katalogfreie Perception-Kandidaten (`circle`, `line`, `polygon_path`, `text_glyph` oder `color_patch`) auftauchen. Der Lerneffekt wird pro Kandidat im nächsten Arbeitspaket als `generalisiert`, `nur Sonderfall` oder `noch nicht erkannt` dokumentiert.

Der PF8-Linkage-Report wurde als gekoppelte Plan-B-Aufgabe erneut auf die neue GE1001/GE9021-Rotation ausgerichtet (`2/2` Samples mit dokumentiertem Perception-Lerneffekt): `GE1001_M` ist für Kreis-/Linien-Seeds `generalisiert`, `GE9021_7M` liefert zunächst einen Linienhinweis als `nur Sonderfall`.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
