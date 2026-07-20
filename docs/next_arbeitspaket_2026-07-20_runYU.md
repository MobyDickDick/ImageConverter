# Nächstes Arbeitspaket – GE9013_1M 4096th-Yoctofine-Opacity-Probes Run YU (2026-07-20)

Run YU rotiert nach `docs/next_arbeitspaket_2026-07-20_runYT.md` wieder in
die aktive Plan-B-Kandidatenliste zu `GE9013_1M`. Der Fokus bleibt
katalogfrei: Die allgemeinen `ColorPatch`- und `RectBorder`-Opacity-Probes
werden um eine 4096th-yoctofeine Zwischenstufe direkt um die bisherige
BackBottom-Zielopacity ergänzt.

## Umsetzung

- Die allgemeine Geometry-IR-Optimierung probt bei `ColorPatch.fill_opacity`
  zusätzlich `0.982812488079071044921875` als 4096th-yoctofeine Zwischenstufe
  unterhalb von `0.9828125`.
- Die allgemeine Geometry-IR-Optimierung probt bei `RectBorder.stroke_opacity`
  zusätzlich `0.982812511920928955078125` als 4096th-yoctofeine Zwischenstufe
  oberhalb von `0.9828125`.
- Zwei neue Helper-Tests sichern, dass die neuen Opacity-Probes nur über den
  regulären Optimiererpfad und nur bei sinkendem Fehler akzeptiert werden.
- Die Änderung hängt weder an `GE9013_1M` noch an eine andere Runtime-Bild-ID.

## Plan-B-/Perception-Lerneffekt

`GE9013_1M` bleibt ein beschreibungsbasierter BackBottom-/hellgraues-Quadrat-
Contract. Run YU erweitert nicht die reine Bilddetektion, sondern den
allgemeinen Registrierungsraum für vorhandene rechteckige Füll- und
Konturelemente. Der Perception-Lerneffekt bleibt auf Ebene der Seed-Quelle
`nur Sonderfall`, die nachgelagerte Opacity-Registrierung ist aber katalogfrei
generalisiert.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_color_patch_opacity_with_4096th_yoctofine_probe tests/detailtests/test_geometry_ir_optimizer_helpers.py::test_default_optimizer_refines_rect_border_stroke_opacity_with_4096th_yoctofine_probe` läuft grün mit `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün mit `0 occurrences`.

## Ergebnis / nächster Schritt

Run YU schließt den dokumentierten GE9013_1M-Feinschritt auf Code- und
Helper-Test-Ebene ab. Rechteckige Füll- und Konturelemente können nun eine
4096th-yoctofeine Opacity-Zwischenregistrierung nutzen. Das nächste
Arbeitspaket kann in der aktiven Plan-B-Rotation zu `DLG0021` wechseln oder
weitere allgemeine BackBottom-/Rechteck-Feinregistrierung prüfen.
