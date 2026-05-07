# T5-Kurzlauf Run CI (AC0812-Timeoutpfad, Python 3.10)

- **Datum:** 2026-05-07
- **Befehl:** `PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q | tee artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-07_runCI.log`
- **Exit-Code:** `0`
- **Ergebnis:** `1 passed, 5 warnings in 101.93s`
- **Artefakt:** `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-07_runCI.log`

## Kurzfazit

Der komplementäre AC0812-Isolationspfad läuft in der bestätigten Python-`3.10.20`-Umgebung stabil mit Exit `0` und ohne Timeout. Damit liegen für AC0811- und AC0812-Teilpfade aktuelle, reproduzierbare T5-Nachweise auf derselben Toolchain vor.
