# FALLBACK-GROUPS-CHECKER-04 – separat eingefrorener unabhängiger Prüfer

[Umsetzung, Ergebnisse und Grenzen](../../../docs/next_arbeitspaket_2026-11-13_fallback_checker.md).

`manifest.json` enthält fünf explizite synthetische Objekt-/Relationsannotationen
und ihre XML-Positivszenen. `checker.py` und `evaluator.py` bewahren den separat
eingefrorenen Code; `seal.json` bindet alle drei Dateien. Die produktive Runtime
ist kein Bestandteil des Prüfers. Der Replay verweigert abweichenden Code.
`summary.json` enthält fünf positive Entscheide, 60 zurückgewiesene Kontrollen
mit beiden Rendererdiagnosen und 18 historische Ausgaben mit SHA-256.
Die Kandidaten stehen vollständig unter `historical/` und sind keine Reserven.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_fallback_checker --output .tmp/fallback-checker-replay --historical artifacts/evaluation/fallback_checker_v1/historical
.venv/Scripts/python.exe -m pytest -q tests/test_fallback_checker.py tests/test_fallback_composition.py tests/test_fallback_groups.py tests/test_fallback_structure.py tests/test_real_composition_holdout_freeze.py
.venv/Scripts/python.exe -m tools.run_pytest_profile core-green
```

Python 3.10, `requirements-dev.txt` und `rsvg-convert` werden benötigt.
Zielordner müssen neu sein. `--freeze NEUER_ORDNER` bereitet ausschließlich
einen neuen Entwicklungsstand vor und überschreibt diesen Stand nicht.
Programmatische Prüfung: `tools.check_native_scene.check_scene(svg, annotation)`.
Die annotierte native Einzelprimitivdarstellung ist verbindlich; äquivalente
Segmentierungen, beliebige Kurven, Transparenz, CSS und allgemeine affine
Transformationen sind keine positive Abnahme. Der Prüfer verifiziert bekannte
verdeckte synthetische Teile, behauptet aber keine Sichtbarkeit verdeckter realer
Geometrie. Es gab null neue CLI-Versuche und null reservierte Versuche.
Alle realen Familien bleiben `sealed_unrun`; Kurvenprüfer und menschlicher
Annotationsaudit fehlen. Keine neue Modellfreigabe oder Archivpromotion.
