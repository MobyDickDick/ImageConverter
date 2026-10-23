# T5-Kurzlauf Run CW (AC0812-Timeoutpfad, Python 3.10)

- **Datum:** 2026-05-11
- **Befehl:** `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q | tee artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-11_runCW.log`
- **Exit-Code:** `0`
- **Ergebnis:** `1 passed, 5 warnings in 92.93s`
- **Artefakt:** `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-11_runCW.log`

## Kurzfazit

Der AC0812-Isolationspfad ist in der bestätigten Python-`3.10.20`-Toolchain erneut stabil reproduzierbar (Exit `0`, ohne Timeout). Damit liegt ein aktueller T5-Nachweis vor, der als leichter Rotationsschritt vor dem nächsten N1/N2-Vollbereichslauf dokumentiert ist.
