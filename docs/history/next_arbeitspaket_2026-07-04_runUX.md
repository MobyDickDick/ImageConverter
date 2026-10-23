# Nächstes Arbeitspaket – GE9012_6M Nanofine-Opacity-Probes + US-Flag-Plan-B Run UX (2026-07-04)

Run UX rotiert nach dem SE0041_1-Rule-Stroke-Feinschritt auf den aktiven
Plan-B-Kandidaten `GE9012_6M`. Der Fokus bleibt katalogfrei: Die bestehenden
`ColorPatch`-/`RectBorder`-Opacity-Probes erhalten zusätzliche nanofeine
Zwischenwerte, damit hellgraue Quadratflächen und Konturen in BackBottom-
ähnlichen Beschreibungen pixelnäher bewertet werden können.

## 1) Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt für `ColorPatch` und
  `RectBorder` zusätzlich zu den vorhandenen 0,003125er-Microfine-Stufen nun
  nanofeine 0,0015625er-Zwischenwerte um die kritischen Bereiche `0.9125` bis
  `0.91875` sowie `0.98125` bis `0.9875`.
- Die neuen Probes gelten neutral für flächen- und rechteckbasierte IR-Elemente
  und werden wie alle Elementprobes nur übernommen, wenn der gerenderte Fehler
  im Elementschritt strikt sinkt.
- Die Änderung ist deterministisch und katalogfrei; sie koppelt weder an
  `GE9012_6M` noch an eine andere Runtime-Bild-ID.

## 2) Gekoppelte Plan-B-Aufgabe: SVG-Textbeschreibung

Zum eingereichten SVG wurde eine formalisierte Textbeschreibung erzeugt:

> Rechteckige US-Flagge im Seitenverhältnis 1,9:1 mit dreizehn waagerechten,
> gleich hohen Streifen, beginnend und endend mit Rot. Die roten Streifen sind
> dunkelrot, die alternierenden Streifen weiß. Links oben liegt ein dunkelblaues
> Kanton-Rechteck, das sieben Streifen hoch und etwa 40 Prozent der Flaggenbreite
> breit ist. Im Kanton stehen fünfzig weiße fünfzackige Sterne in versetzten
> Reihen: sechs Reihen mit je sechs Sternen und fünf dazwischen liegende Reihen
> mit je fünf Sternen. Die Sterne sind regelmäßig gerastert und gleich groß.

Diese Beschreibung ist bewusst katalogfrei formuliert: Sie beschreibt
Geometrie, Farben und Sternraster des SVGs, ohne eine gespeicherte Sample-Datei
oder eine Bild-ID als Lösungsweg vorauszusetzen. Der Anlass am 250. Jahrestag
der Unabhängigkeitserklärung ist fachlich passend dokumentiert; technisch bleibt
Plan B ein normaler Beschreibung-zu-Geometrie-Nachweis.

## 3) Perception-Lerneffekt

`GE9012_6M` bleibt ein beschreibungsbasierter Sonderfall für das
BackBottom-/hellgraues-Quadrat-Vokabular. Run UX erweitert nicht die reine
Bilddetektion, sondern den allgemeinen Optimierungsraum für vorhandene
`ColorPatch`-/`RectBorder`-Opacity-Werte, wie sie aus neutral beschriebenen
hellen Rechteckflächen entstehen.

## 4) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_nanofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_nanofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_microfine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_microfine_probe` läuft grün mit `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge9012-runUX --start GE9012_6M --end GE9012_6M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; die isolierte GE9012_6M-Metrik bleibt stabil bei `Mean-Delta²=15386.639648` und `Fehler/Pixel=0.044122`.

## 5) Ergebnis / nächster Schritt

Run UX schließt den dokumentierten GE9012_6M-Feinschritt ab. Rechteck- und
Füllflächen-Opacity kann nun katalogfrei nanofeine Zwischenwerte bewerten; der
isolierte GE9012_6M-Einzellauf bleibt metrisch stabil. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder
weitere allgemeine Bild-/Beschreibung-Fusion untersuchen.
