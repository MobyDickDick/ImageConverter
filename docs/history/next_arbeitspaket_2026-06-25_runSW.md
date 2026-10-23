# Nächstes Arbeitspaket – Plan-B GE9013_1M Vertical BackBottom-Scale Run SW (2026-06-25)

Run SW arbeitet nach Run SV den nächsten dokumentierten Plan-B-Kandidaten aus `PLAN_B_KANDIDATEN.md` ab: **GE9013_1M**.

## Ausgangspunkt

- `GE9013_1M` ist der fünfte aktive Diff-Fall der Run-SR-Triage (`mean_delta2=16001.943359375`, `normalized_mse=0.0820296981129053`).
- Die Beschreibung lautet wie bei GE9012: `Wie BackBottom: hellgraues Quadrat. . Geometrische Variante: identisch zur Referenz.`
- Anders als `GE9012_6M` nutzt `GE9013_1M` eine schmale, hohe Zeichenfläche (`20×60`). Das Arbeitspaket prüft daher, dass der Run-SV-Contract nicht unbemerkt an die breite GE9012-Geometrie gekoppelt ist.

## Umsetzung

- Der katalogfreie BackBottom-/`hellgraues Quadrat`-Contract bleibt ein normierter vollflächiger `RectBorder` mit hellgrauer Füllung, ohne Stroke und mit `light_grey_square_decomposition_v1`.
- Ein zusätzlicher Regressionstest rendert dieselbe BackBottom-Aliasbeschreibung auf einer neutralen vertikalen `20×60`-Zeichenfläche und erwartet eine vollflächige SVG-Rect-Ausgabe.
- Der Test prüft außerdem, dass kein `GE9013`-Token in der SVG-Ausgabe auftaucht; die Skalierung kommt ausschließlich aus Canvas-Größe und normierter Geometry-IR.

## Ergebnis

- Perception-Lerneffekt für `GE9013_1M`: `nur Sonderfall` – Bilddetektion liefert zwar Linien-/Rechteckhinweise, der robuste Seed bleibt aber der beschreibungsbasierte, katalogfreie Light-Grey-Square-Contract.
- Pixel-Feintuning bleibt offen: Der lokale GE9013-Konvertierungslauf fällt weiterhin auf die elementweise Plan-B-Annäherung zurück und verbessert die harte Pixelmetrik noch nicht.
- Die aktive Kandidatenrotation bleibt unverändert, weil der Review ohne neue allgemeine Converted-SVG-Baseline weiterhin dieselben fünf Diff-Fälle führt.

## Prüfungen

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/test_image_composite_converter.py -k 'backbottom_square'` → grün.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python src/imageCompositeConverter.py --mode convert --input-dir artifacts/images_to_convert --csv-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start GE9013 --end GE9013 --iterations 64 --deterministic-order` → grün; protokolliert weiterhin den elementweisen Fallback als pixelnähere Variante.
