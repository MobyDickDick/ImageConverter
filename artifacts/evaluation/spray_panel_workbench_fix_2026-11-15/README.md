# Luftbefeuchter: zwei Plan-B-Fehlläufe korrigiert

[Diagnose, Änderungen und Grenzen](../../../docs/spray_panel_workbench_2026-11-15.md).

Die unveränderte Nutzereingabe liegt lokal unter `imported/`.
`fresh_cli/` enthält frisch vorbereitete Raster mit dem Seed aus dem ZIP,
zwei getrennt erhaltene Versuche und die vollständigen CLI-Berichte.
`attempt_0002` ist der abschliessende Versuch: beide Fälle bestehen.

- [Original, neue SVG](fresh_cli/attempts/attempt_0002/original/conversion/converted_svgs/original.svg)
- [Erste Variante, neue SVG](fresh_cli/attempts/attempt_0002/probe_01/conversion/converted_svgs/probe_01.svg)
- [Workbench-Bericht](fresh_cli/report.json)
- [CLI-Zusammenfassung](replay_final.log)
- [Unabhängige Rendererprüfung](verification.json)
- [135 Regressionen](regression_tests_final.log)
- [Zusätzlicher vollständiger Variantenfit](variant_regression.log)
- [Kompakter, versionierter Nachweis](summary.json)

Die generierten Raster, SVGs und vollständigen Protokolle bleiben gemäss
Projektkonvention lokal. Dauerhafte Tests verwenden die eingecheckte
SVG unter `tests/fixtures/spray_panel_workbench.svg` und die unveränderte
Nutzerbeschreibung unter `tests/fixtures/descriptions/`.

Reproduktion aus dem Projektverzeichnis (PowerShell):

```powershell
$env:PYTHONPATH = '.'
.venv/Scripts/python.exe artifacts/evaluation/spray_panel_workbench_fix_2026-11-15/replay.py
.venv/Scripts/python.exe -m pytest tests/test_spray_panel.py tests/test_dashed_spray.py tests/test_spray_panel_workbench.py tests/test_dashed_rectangles.py tests/detailtests/test_plan_b_workbench.py -q
```

`replay.py` verwendet das lokal erhaltene ZIP und legt weitere Versuche an.
Eine Reproduktion ohne lokale Studienartefakte ist über die genannten Tests
möglich. Für die Workbench-HTTP-Tests muss lokales Socket-Binding erlaubt sein.
