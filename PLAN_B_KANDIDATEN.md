# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-19, Review-Refresh Run RC)

Der reproduzierbare Review mit `tools/review_conversion_quality.py` findet wieder
qualifizierte Diff-Fälle oberhalb der Review-Grenze. Die Reihenfolge folgt der
automatisch erzeugten Triage `artifacts/evaluation/conversion_quality_review_v2/plan_b_candidate_triage_v1.csv` und wird in
`docs/conversion_quality_review_2026-06-19_runRC.md` begründet. Wichtig: Die
Review-Grenze ist nur ein grobes technisches Gate; die harte Pixelnähe-Metrik
`mean_delta2 <= 18.000` zeigt weiterhin, dass nahezu alle Diff-Paare sichtbar
verbesserungsbedürftig sind.

1. `GE9002_7S` – höchster `normalized_mse`-Fehler der kompakten Plan-B-Triage.
2. `GE9002_5S` – zweithöchster Fehler in derselben einfachen GE9002-Familie.
3. `GE9002_3S` – weiterer kompakter Hochfehlerfall.
4. `GE9002_4M` – mittlere Variante mit weiterhin sehr großem Diff-Abstand.
5. `GE9002_1S` – fünfter automatisch priorisierter GE9002-Fall.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Die neue Run-RC-Triage verschiebt die aktive Rotation von AC08-Badges auf die
GE9002-Diff-Familie. Vor der konkreten Nachzeichnung ist für den jeweils ersten
Kandidaten zu prüfen, ob die dominanten Primitive bereits als katalogfreie
Perception-Kandidaten (`circle`, `line`, `polygon_path`, `text_glyph` oder
`color_patch`) auftauchen. Der Lerneffekt wird pro Kandidat im nächsten
Arbeitspaket als `generalisiert`, `nur Sonderfall` oder `noch nicht erkannt`
dokumentiert.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
