# Nächstes Arbeitspaket – Plan-B SE0041_1 Square-Badge-Contract Run SU (2026-06-25)

Run SU arbeitet nach Run ST den nächsten dokumentierten Plan-B-Kandidaten aus `PLAN_B_KANDIDATEN.md` ab: **SE0041_1**.

## Ausgangspunkt

- `SE0041_1` war in der Run-SR-Triage der dritte aktive Diff-Fall (`mean_delta2=22543.97265625`, `normalized_mse=0.11556566785210816`).
- Der PF8-Linkage-Report führte den Perception-Lerneffekt bisher als `noch nicht erkannt`; vor der Plan-B-Umsetzung war daher eine zusätzliche Detector-/ROI-Regel oder eine manuelle Seed-Annahme zu dokumentieren.
- Die Beschreibung lautet: `Wie AC0811, jecoch ist der Kreis viereckig anstatt rund gezeichnet.` Damit ist die robuste, katalogfreie Seed-Annahme: AC0811-Stammgeometrie übernehmen, aber den Kopf als neutrales Viereck statt als Kreis rendern.

## Umsetzung

- Die Referenzvererbung akzeptiert jetzt AC08-Referenzen auch dann, wenn im lokalen Rohbeschreibungs-Dictionary kein expliziter Referenztext vorhanden ist. Das macht aliasbasierte `Wie AC0811`-Beschreibungen stabiler testbar.
- Für Beschreibungen mit `viereckig` und `anstatt/statt rund` wird der geerbte Semantic-Badge-Kopf auf `head_style=square_badge` gesetzt und der Elementvertrag von Kreis- auf Viereck-Terminologie umgeschrieben.
- Der Semantic-Badge-SVG-Renderer unterstützt `head_style=square_badge` als rechteckigen Kopf mit derselben Mittelpunkt-/Radius-Signatur wie der bisherige Kreis. Sparse Square-Badge-Parameter werden dabei nicht mehr versehentlich als AC0223-Valve-Head rekonstruiert.
- Regressionstests sichern sowohl den SE0041-Aliasvertrag als auch das SVG-Rendering ohne `<circle>` ab.

## Ergebnis

- Perception-Lerneffekt für `SE0041_1`: `nur Sonderfall` – die reine Bilddetektion erkennt die gewünschte Kopfgeometrie weiterhin nicht ausreichend, aber die dokumentierte Beschreibung liefert eine neutrale, katalogfreie Seed-Annahme (`square_badge` statt Kreis) auf Basis generischer Viereck-Geometrie.
- Pixel-Feintuning bleibt offen: Der lokale Einzelkonvertierungslauf protokolliert den Square-Badge-Contract, fällt für `SE0041_1` aber weiterhin auf die elementweise Plan-B-Annäherung zurück und verbessert die harte Pixelmetrik noch nicht.
- Der Review wurde anschließend mit `tools/review_conversion_quality.py --max-candidates 5` reproduzierbar erneuert; die aktive Kandidatenrotation bleibt unverändert (`DLG0021`, `GE1410_L`, `SE0041_1`, `GE9012_6M`, `GE9013_1M`).

## Prüfungen

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/test_image_composite_converter.py -k 'se0041_square_badge_override or square_badge_head'` → grün.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python src/imageCompositeConverter.py --mode convert --input-dir artifacts/images_to_convert --csv-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start SE0041 --end SE0041 --iterations 64 --deterministic-order` → grün; protokolliert den Square-Badge-Contract, ohne die bestehende SE0041_1-Pixelmetrik zu verbessern.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/review_conversion_quality.py --max-candidates 5` → grün; Kandidatenrotation unverändert.
