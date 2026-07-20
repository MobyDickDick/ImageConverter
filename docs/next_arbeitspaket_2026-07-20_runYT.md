# Nächstes Arbeitspaket – Smooth-Gradient statt Stripe-Pixel-Fit Run YT (2026-07-20)

Run YT arbeitet nach `docs/next_arbeitspaket_2026-07-19_runYS.md` den nächsten dokumentierten Anschluss ab und überprüft explizit die Nutzeranforderung, dass gradientenartige Flächen nicht mehr als dünne Streifen-/Band-Pixel-Fits ausgegeben werden.

## Umsetzung

- Die Non-Composite-Auswahl erkennt veraltete streifenartige Raster-Fit-SVGs bei beschreibungsdeklarierten Farbverläufen und lässt sie nicht mehr eine semantische `HorizontalGradient`-Geometry-IR-Ausgabe verdrängen.
- Echte SVG-Verläufe (`linearGradient`/`radialGradient`) bleiben ausdrücklich zulässig, damit glatte Farbverläufe weiterhin optimiert und gerendert werden können.
- Die Erkennung ist katalogfrei: Sie hängt weder an `AC0010` noch an andere Runtime-Bild-IDs, sondern an der Kombination aus Gradientenbeschreibung und streifenartiger SVG-Ausgabe ohne echten Verlauf.

## Plan-B-/Perception-Lerneffekt

Run YT erweitert nicht die reine Bilddetektion. Der Lerneffekt ist `generalisiert` für den nachgelagerten Non-Composite-Auswahlpfad: Bei Gradientenbeschreibungen darf ein niedrig bewerteter Legacy-Stripe-Pixel-Fit nicht mehr gegen einen glatten Verlauf gewinnen.

## Validierung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_non_composite_runtime_helpers.py::test_ac0010_rejects_deprecated_stripe_fit_even_when_pixel_error_is_lower tests/detailtests/test_non_composite_runtime_helpers.py::test_deprecated_stripe_fit_detector_allows_real_linear_gradients tests/detailtests/test_non_composite_runtime_helpers.py::test_description_geometry_candidate_yields_to_much_better_algorithmic_raster_fit` läuft grün mit `3 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_gradient_stripe_strategy_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py::test_run_non_composite_iteration_impl_ignores_gradient_stripe_strategy` läuft grün mit `6 passed`.

## Ergebnis / nächster Schritt

Run YT schließt den dokumentierten Smooth-Gradient-Anschluss auf Code- und Testebene ab. Die Tests bestätigen, dass nur echte Farbverläufe akzeptiert werden, während ein alter `generic-stripe-pixel-fit` trotz besserer Pixelmetrik nicht mehr ausgewählt wird. Das nächste Arbeitspaket kann wieder in der aktiven Plan-B-Rotation zu `GE9013_1M` wechseln oder weitere allgemeine Gradienten-/Antialiasing-Feintuning-Schritte prüfen.
