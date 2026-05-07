# T5 AC0812 Blocker Probe — Run CG (2026-05-07)

- **Anlass:** In `docs/open_tasks.md` als nächster Schritt dokumentierte Wiederholung des T5-Kurzlaufs in der lauffähigen Python-`3.10.20`-Umgebung.
- **Befehl:** `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius -q | tee artifacts/converted_images/reports/T5_ac0812_blocker_probe_2026-05-07_runCG.log`
- **Exit-Code:** `0`
- **Ergebnis:** `1 passed` in `117.32s`.
- **Warnungen:** 5 DeprecationWarnings aus Swig/MuPDF-Bindings (`SwigPyPacked`, `SwigPyObject`, `swigvarlink`).

## Kurzfazit

Der zuvor unter Python `3.12` nur `SKIPPED` gelaufene T5-Kurztest ist in der dokumentierten Zielumgebung Python `3.10.20` erfolgreich reproduzierbar durchgelaufen. Damit liegt ein neues, verwertbares T5-Artefakt ohne OpenCV/Numpy-Importblocker vor.
