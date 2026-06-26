# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-06-25, Review-Refresh Run SR)

Der reproduzierbare Review mit `tools/review_conversion_quality.py --max-candidates 5` rotiert nach dem abgeschlossenen `GE9021_7M`-Qualitätsrefresh auf fünf qualifizierte Diff-Fälle oberhalb der Review-Grenze. Die Reihenfolge folgt der automatisch erzeugten Triage `artifacts/evaluation/conversion_quality_review_v2/plan_b_candidate_triage_v1.csv`. Wichtig: Die Review-Grenze ist nur ein grobes technisches Gate; die harte Pixelnähe-Metrik `mean_delta2 <= 18.000` zeigt weiterhin, dass alle fünf Diff-Paare sichtbar verbesserungsbedürftig sind.

1. `DLG0021` – höchster aktueller kompakter Diff-Fehler der Triage (`mean_delta2=24856.818359375`, `normalized_mse=0.1274218549756504`); Run SS ergänzt einen katalogfreien Description-Geometry-IR-Pfad, Run SX ergänzt den beschriebenen vertikalen Checkmark-Stroke-Gradienten, Geometrie-/Pixel-Feintuning bleibt offen.
2. `GE1410_L` – zweiter aktueller kompakter Diff-Fall oberhalb der Review-Grenze (`mean_delta2=24170.25390625`, `normalized_mse=0.12390236527617583`); Run ST ergänzt einen katalogfreien Diagramm-/Dreieck-Primitive-Contract, Pixel-Feintuning bleibt offen.
3. `SE0041_1` – dritter aktueller Diff-Fall mit mittlerer Symbolfläche (`mean_delta2=22543.97265625`, `normalized_mse=0.11556566785210816`); Run SU ergänzt einen katalogfreien Square-Badge-Seed aus der AC0811-Aliasbeschreibung, Pixel-Feintuning bleibt offen.
4. `GE9012_6M` – breiter GE-Diff-Fall oberhalb der Review-Grenze (`mean_delta2=16423.2109375`, `normalized_mse=0.08418921408432654`); Run SV ergänzt einen katalogfreien BackBottom-/Light-Grey-Square-Geometry-IR-Contract, Pixel-Feintuning bleibt offen.
5. `GE9013_1M` – schmaler GE-Diff-Fall oberhalb der Review-Grenze (`mean_delta2=16001.943359375`, `normalized_mse=0.0820296981129053`); Run SW sichert den katalogfreien BackBottom-/Light-Grey-Square-Contract zusätzlich für die vertikale 20×60-Canvas-Skalierung ab, Pixel-Feintuning bleibt offen.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Die Run-SR-Triage ersetzt die erledigte `GE1001_M`/`GE9021_7M`-Rotation durch fünf kleinere Diff-Fälle. Vor der konkreten Nachzeichnung ist für `DLG0021` zu prüfen, ob die dominanten grafischen Primitive bereits als katalogfreie Perception-Kandidaten (`color_patch`, `polygon_path`, `line`, `rectangle` oder `text_glyph`) auftauchen. Der Lerneffekt wird pro Kandidat im nächsten Arbeitspaket als `generalisiert`, `nur Sonderfall` oder `noch nicht erkannt` dokumentiert.

Der PF8-Linkage-Report wurde als gekoppelte Plan-B-Aufgabe erneut auf die neue Rotation ausgerichtet (`5/5` Samples mit dokumentiertem Perception-Lerneffekt): `GE1410_L` ist seit Run ST für Achsen-/Linien- und Dreieck-Seeds `generalisiert`, `GE9012_6M` besitzt seit Run SV einen beschreibungsbasierten Sonderfall-Contract für das BackBottom-/hellgraues-Quadrat-Vokabular, `GE9013_1M` besitzt seit Run SW denselben beschreibungsbasierten Sonderfall-Contract und eine vertikale Canvas-Skalierungsabsicherung, während `SE0041_1` seit Run SU als Sonderfall eine manuelle, beschreibungsbasierte Square-Badge-Seed-Annahme nutzt. Für `DLG0021` ist die manuelle Seed-Annahme seit Run SS als neutraler Checkbox-/Haken-Primitive-Contract dokumentiert; Run SX ergänzt daran katalogfrei den beschriebenen grünen Vertikalgradienten. Die reine Bilddetektion bleibt weiterhin nicht ausreichend.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
