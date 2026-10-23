# T5-Kurzlauf Run CO (AC0811-Timeoutpfad, Python 3.10)

- **Datum:** 2026-05-09
- **Befehl:** `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0811_only -q | tee artifacts/converted_images/reports/T5_ac0811_timeoutpath_probe_2026-05-09_runCO.log`
- **Exit-Code:** `0`
- **Ergebnis:** `1 passed, 5 warnings in 112.96s`
- **Artefakt:** `artifacts/converted_images/reports/T5_ac0811_timeoutpath_probe_2026-05-09_runCO.log`

## Kurzfazit

Der AC0811-Isolationspfad bleibt in der Python-`3.10.20`-Toolchain stabil reproduzierbar mit Exit `0` und ohne Timeout. Damit ist erneut ein aktueller T5-Nachweis vorhanden, der vor dem nächsten N1/N2-Vollbereichslauf als leichter Rotationsschritt dokumentiert ist.
