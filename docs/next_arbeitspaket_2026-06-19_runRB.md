# Nächstes Arbeitspaket – IDO-17 Elementvalidierungs-Diagnostik-De-ID Run RB (2026-06-19)

Run RB setzt IDO-17 aus `docs/image_description_only_tasks.md` fort und
entfernt zwei verbliebene katalogspezifische Diagnoseentscheidungen aus der
Elementvalidierung.

## 1) Ziel

Budget-Floor und Deep-Trace sollen weiterhin für fokussierte, teure
Elementvalidierungsfälle verfügbar sein, aber nicht mehr anhand einer konkreten
Bild-/Katalog-ID aktiviert werden.

## 2) Umsetzung

- `validateBadgeByElementsImpl(...)` liest den optionalen neutralen Parameter
  `validation_time_budget_floor_sec` und hebt damit ein explizites
  `validation_time_budget_sec` an, ohne den Variantennamen auszuwerten.
- Deep-Trace-Logging wird über `validation_deep_trace_enabled` aktiviert; der
  Log-Präfix kommt aus `validation_deep_trace_label` und fällt auf
  `element_validation_deep_trace` zurück.
- Die bisherigen direkten Anker-Variantenvergleiche und ID-haltigen
  Diagnosekommentare wurden aus der Elementvalidierung entfernt.
- Die Regressionstests nutzen katalogfreie Varianten (`ZZWORKLOAD`, `ZZTRACE`)
  und prüfen Budget-Floor sowie Deep-Trace weiterhin isoliert.

## 3) Nachweis

- `python -m compileall -q src tests/test_image_composite_converter.py`
  → Exit `0`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_validate_badge_by_elements_applies_neutral_budget_floor tests/test_image_composite_converter.py::test_validate_badge_by_elements_logs_deep_trace_from_neutral_flag`
  → `2 passed`.
- `python tools/check_no_new_image_id_hardcoding.py`
  → `PASS: no image-ID hardcoding above legacy baseline (316 legacy occurrences remain).`

## 4) Ergebnis

IDO-17 baut die Legacy-Baseline weiter ab: Die Elementvalidierungs-Diagnostik
entscheidet nicht mehr über konkrete Runtime-Katalog-IDs; der Ratchet sinkt von
317 auf 316 Runtime-ID-Vorkommen.

## 5) Nächster Schritt

IDO-17 fortsetzen und den nächsten verbleibenden katalogspezifischen Runtime-
Guard durch messbare Parameter, neutrale Metadaten oder reine Testdaten ersetzen.
