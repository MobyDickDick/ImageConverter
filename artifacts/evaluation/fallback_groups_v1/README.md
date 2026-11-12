# FALLBACK-GROUPS-02 – bekannte Entwicklungsfälle und synthetische Varianten

Die [Umsetzung und Grenzen](../../../docs/next_arbeitspaket_2026-11-12_fallback_groups.md)
beschreiben den begrenzten Abschluss. Die versionierte `summary.json` enthält
36 vergleichbare Fortsetzungen, acht echte CLI-Läufe, 48 synthetische
Ablationen und 33 beschädigte Kontrollen, jeweils mit beiden Renderern.
Der unterbrochene zusätzliche Versuch bleibt separat erhalten.

`inputs/` sichert die beiden bisherigen Fortsetzungsmodule, die bekannte
Entwicklungsmanifestkopie und Hashes vor Runtimeänderung. Die Originale liegen
unverändert in `../fallback_structure_v1/inputs/`. `freeze/` enthält zwei
zusätzliche gesperrte reale Kompositionsfamilien mit Originalbytes,
Beschreibungen, sichtbaren Objekt-/Relationsmarkierungen und Runtimehashes.
Diese Reserven wurden nicht konvertiert; eine positive Familienabnahme wird
nicht behauptet. Historische Katalogexposition ist ausdrücklich dokumentiert.

```powershell
python -m tools.freeze_real_composition_holdouts --verify artifacts/evaluation/fallback_groups_v1/freeze/manifest.json
python -m tools.evaluate_fallback_groups --output .tmp/fallback-groups-replay --cli
python -m tools.evaluate_fallback_groups --output .tmp/fallback-groups-replay --review
python -m pytest -q tests/test_fallback_groups.py tests/test_fallback_structure.py tests/test_search_minimum_effort.py tests/test_image_converter_sample.py tests/test_search_portfolio.py tests/test_conversion_search_scheduler.py tests/test_adaptive_conversion_search.py tests/test_conversion_persistence.py tests/detailtests/test_iteration_initialization_helpers.py tests/detailtests/test_iteration_runtime_helpers.py tests/test_satisfactory_archive.py tests/test_catalog_inventory.py tests/test_real_composition_holdout_freeze.py -k "not every_archived_satisfactory_image_is_reconverted_and_checked"
python -m tools.run_pytest_profile core-green
```

Python 3.10.11 aus `.venv`, NumPy/OpenCV/Pillow/PyMuPDF und unabhängiges
`rsvg-convert` werden benötigt. Die Studienaufrufe verwenden existierende
Windows-Wachhaltung für aktive Suche. Beobachtungslücken oberhalb 250 ms über
dem Bildbudget müssen vor `--review` mit `--repeat-interrupted` separat erhalten
und wiederholt werden; frühere SVGs werden dabei nicht überschrieben.

Raw-SVGs, Suchprotokolle und CLI-Bäume bleiben lokal in
`.tmp/fallback-groups-final/` oder entstehen beim Replay neu. Produktiv stehen
`ICC_FALLBACK_STRUCTURE_MODE=off|primitives|lines|legacy_combined|groups|combined`
für Ablationen bereit, Standard ist `combined`. `legacy_combined` deaktiviert
die neuen Gruppen; der eingefrorene Fortsetzungsvergleich verwendet zusätzlich
die tatsächlichen alten Module. Alle Pixelpässe bleiben unvalidierte Entwürfe.
