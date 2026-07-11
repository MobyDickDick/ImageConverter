# Nächstes Arbeitspaket – GE1410_L Quarter-Yoctofine-PolygonPath-Probes Run XJ (2026-07-11)

Run XJ rotiert nach `docs/next_arbeitspaket_2026-07-11_runXI.md` in der
aktiven Plan-B-Kandidatenliste zu `GE1410_L`. Der Fokus bleibt katalogfrei:
Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten eine
quarter-yoctofeine Zwischenstufe für antialiasing-empfindliche Diagramm- und
Dreiecksprimitive.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `PolygonPath`-Punkten
  zusätzlich `±0.00000244140625` im normierten Koordinatenraum.
- Dieselbe quarter-yoctofeine absolute Zwischenstufe wird für
  `PolygonPath`-`stroke_width` geprüft.
- Zwei neue Helper-Tests sichern, dass beide Probes ausschließlich über den
  regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `GE1410_L` noch an eine andere Runtime-Bild-ID.

## Neue Sample-basierte Plan-B-Aufgaben

Die zwei zuletzt hinzugefügten Sample-SVGs werden als separate Ad-hoc-Plan-B-
Contracts geführt und verdrängen die fünf automatisch triagierten aktiven
Kandidaten nicht:

- `AC0213_L` (`artifacts/images_to_convert/samples/AC0213_L.svg`) –
  sample-basierte Generalisierungsaufgabe für ein linksorientiertes
  Ventilsymbol mit grauem Verlaufskörper, Leitungsanschlüssen und `M`-Glyph.
  Plan-B-Ziel: SVG→Raster→SVG-Roundtrip mit neutralen Ventilkopf-, Connector-,
  Gradienten- und Text-Glyph-Primitiven statt numerischer Sample-Kopie.
- `AC0552_2_L` (`artifacts/images_to_convert/samples/AC0552_2_L.svg`) –
  sample-basierte Generalisierungsaufgabe für ein flaches grünes
  Chevron-/Pfeilsegment mit mehrstufigem Vertikalgradienten und beschnittener
  Innenkontur. Plan-B-Ziel: Roundtrip über katalogfreie PolygonPath-,
  Clip-/BBox- und Gradient-Stop-Primitives.

## Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt für Achsen-/Linien- und Dreieck-Seeds generalisiert. Run XJ
erweitert nicht die reine Bilddetektion, sondern den allgemeinen
Registrierungsraum vorhandener Polygonpfade. Der Perception-Lerneffekt bleibt
`generalisiert`, die neue Probe ist katalogfrei.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_points_with_quarter_yoctofine_subpixel_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_polygon_path_stroke_width_with_quarter_yoctofine_absolute_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. ICC_MAX_QUALITY_PASSES=1 timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1410-runXJ --start GE1410_L --end GE1410_L --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; der beste Pass meldet `Mean-Delta²=630.313599` und `Fehler/Pixel=0.010486`, der finale Validierungspass `Mean-Delta²=705.599976`.

## Ergebnis

Run XJ schließt den dokumentierten GE1410_L-Feinschritt ab. Polygonpfad-Punkte
und Polygonpfad-Stroke-Widths können nun quarter-yoctofeine absolute Probes
nutzen; der isolierte GE1410_L-Einzellauf bleibt gegenüber der besten
Run-XE-Metrik im gleichen Restfehlerband, verbessert diese aber nicht weiter.
Das nächste Arbeitspaket kann in der aktiven Plan-B-Rotation zu `SE0041_1`
wechseln oder weitere allgemeine Polygon-/Antialiasing-Feinregistrierung
prüfen.
