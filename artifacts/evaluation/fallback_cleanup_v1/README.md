# FALLBACK-GROUPS-CLEANUP-06 – begrenzte synthetische Entwicklung

[Umsetzung, Messumfang und Grenzen](../../../docs/next_arbeitspaket_2026-11-14_fallback_cleanup.md).

`manifest.json` und `seal.json` binden die vor der Runtimeänderung gesicherten
vier Runtimequellen, sechs tatsächlichen PNGs, Beschreibungen, Ausgangs-/Ziel-XMLs,
externen Segmentannotation und unveränderten Seeds/Budgets. Die alten
CHECKER-04/-05-Dateien bleiben separat unverändert versiegelt; jeder Replay
verifiziert CHECKER-05 einschließlich des unveränderten strengen Prüfers.

`results/baseline/` enthält 18 alte direkte Ausgaben und deren Nachmessungen,
`results/current/` die 18 sauberen Ausgaben und 42 Negativentscheidungen.
`results/cli/` enthält sechs echte CLI-SVGs und die unabhängigen Nachprüfungen.
Die CLI-Zusammenfassung bewahrt die ursprünglichen relativen Laufpfade; die
zusätzlich gespeicherten SVGs heißen portabel `composition_00.svg` bis
`composition_05.svg`. `results/seal.json` bindet alle Ergebnisdateien samt
finalem Evaluator und verwendeten Runtimequellen. Raw-Logs und vollständige
CLI-Laufbäume bleiben separat unter `.tmp/fallback-cleanup-*-final` erhalten.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_fallback_cleanup --baseline --output .tmp/fallback-cleanup-baseline-replay
.venv/Scripts/python.exe -m tools.evaluate_fallback_cleanup --output .tmp/fallback-cleanup-replay
.venv/Scripts/python.exe -m tools.evaluate_fallback_cleanup --cli --output .tmp/fallback-cleanup-cli-replay
.venv/Scripts/python.exe -m pytest -q tests/test_fallback_cleanup.py tests/test_segment_checker.py tests/test_fallback_checker.py tests/test_fallback_composition.py tests/test_fallback_groups.py tests/test_fallback_structure.py tests/test_real_composition_holdout_freeze.py tests/test_catalog_inventory.py tests/test_search_minimum_effort.py tests/test_image_converter_sample.py
.venv/Scripts/python.exe -m tools.run_pytest_profile core-green
```

Python 3.10, `requirements-dev.txt` und `rsvg-convert` sind erforderlich.
Alle Zielordner müssen neu sein. `--freeze` erstellt ausschließlich einen
neuen Entwicklungsfreeze und überschreibt die vorhandenen Eingaben nicht.
Die Baseline importiert die gesicherten Runtimequellen; der neue Stand
verwendet den tatsächlichen produktiven Suchweg. Referenz-SVG-Zugriffe werden
im CLI-Worker blockiert. Keine Modellfreigabe wird als Qualitätsnachweis benutzt.

Ergebnis: 0/18 → 18/18 vollständige direkte Inventare, unverändert 18/18
Bild-/Detailabnahmen mit beiden Renderern, 6/6 unabhängige CLI-Abnahmen,
42/42 abgelehnte Gegenproben. Zwölf zusätzliche Kontur-/Duplikatkontrollen
bestehen die Bildgates, bleiben aber Inventarfehler. Bekannte überdeckte
Ausgangsrechtecke werden ersetzt; ausgelassene verdeckte Gestängestücke
bleiben ausdrücklich unbestätigt.

Dieselbe Konstruktion mit Farb- und Ausgangsfehlervarianten ist keine neue
reale Kohorte. Null Reserveversuche, null Modellfreigaben, keine Archivpromotion.
Kurvenprüfung, menschlicher Annotationsaudit und reale Gesamtabnahme fehlen
weiterhin. Ein Zwischenfehler mit noch überdeckten Rechtecken ist unverändert
unter `.tmp/fallback-cleanup-current` erhalten.
