# Nächstes Arbeitspaket – Plan-B GE9012_6M BackBottom-Square-Contract Run SV (2026-06-25)

Run SV arbeitet nach Run SU den nächsten dokumentierten Plan-B-Kandidaten aus `PLAN_B_KANDIDATEN.md` ab: **GE9012_6M**.

## Ausgangspunkt

- `GE9012_6M` ist der vierte aktive Diff-Fall der Run-SR-Triage (`mean_delta2=16423.2109375`, `normalized_mse=0.08418921408432654`).
- Die Beschreibung lautet: `Wie BackBottom: hellgraues Quadrat. . Geometrische Variante: identisch zur Referenz.`
- Vor Run SV erzeugte diese Beschreibung keine Geometry-IR-Constraints, weil `quadrat` nicht als neutraler Rechteck-/Viereck-Hinweis gezählt wurde; der Snapshot stand dadurch bei `no_supported_geometry_constraint`.

## Umsetzung

- Der beschreibungsgetriebene Geometry-IR-Parser akzeptiert `quadrat` jetzt katalogfrei als rechteckiges Primitive.
- BackBottom- bzw. `hellgraues Quadrat`-Beschreibungen werden als vollflächiger `RectBorder`-/ColorPatch-Vertrag `backbottom_light_grey_square` mit hellgrauer Füllung und ohne Stroke modelliert.
- Der Vertrag trägt eine maschinenlesbare Primitive-Decomposition (`light_grey_square_decomposition_v1`), damit der Seed nicht aus der GE9012-Katalog-ID, sondern aus Beschreibungsvokabular und Primitive-Rolle entsteht.
- Ein Regressionstest sichert Geometry-IR, Description-Constraints und SVG-Ausgabe für die BackBottom-Aliasbeschreibung ab.

## Ergebnis

- Perception-Lerneffekt für `GE9012_6M`: `nur Sonderfall` – die Bilddetektion liefert weiterhin keinen ausreichenden generischen Seed, aber die Beschreibung liefert nun einen neutralen, katalogfreien Light-Grey-Square-Contract.
- Pixel-Feintuning bleibt offen: Der lokale GE9012-Konvertierungslauf fällt weiterhin auf die elementweise Plan-B-Annäherung zurück und verbessert die harte Pixelmetrik noch nicht.
- Die aktive Kandidatenrotation bleibt unverändert; der nächste konkrete Plan-B-Kandidat ist `GE9013_1M`.

## Prüfungen

- `PYTHONPATH=vendor/linux-py310/site-packages:. pytest -q tests/test_image_composite_converter.py -k 'backbottom_square or se0041_square_badge_override or square_badge_head'` → grün.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python src/imageCompositeConverter.py --mode convert --input-dir artifacts/images_to_convert --csv-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start GE9012 --end GE9012 --iterations 64 --deterministic-order` → grün; protokolliert weiterhin den elementweisen Fallback als pixelnähere Variante.
