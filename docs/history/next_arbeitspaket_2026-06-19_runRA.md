# Nächstes Arbeitspaket – IDO-17 Quality-Pass-Policy-De-ID Run RA (2026-06-19)

Run RA setzt IDO-17 aus `docs/image_description_only_tasks.md` fort und
entfernt den verbliebenen katalogspezifischen Quality-Pass-Sonderfall aus dem
Runtime-Code.

## 1) Ziel

Die Quality-Pass-Policy soll fokussierte Initial-Pass-only-Diagnostik weiterhin
unterstützen, aber nicht mehr selbst anhand einer konkreten Bild-/Katalog-ID
entscheiden. Stattdessen wird die Entscheidung über neutrale, vom Caller
bereitgestellte Metadaten getroffen.

## 2) Umsetzung

- `resolveMaxQualityPassesImpl(...)` akzeptiert jetzt optional
  `initial_pass_only_base_names` und normalisiert diese Metadaten wie die
  Batch-Basen. `convertRange(...)` kann diese Metadaten katalogfrei aus
  `ICC_INITIAL_PASS_ONLY_BASE_NAMES` übernehmen.
- Der bisherige harte Spezialfall wurde durch die neutrale Policy-Begründung
  `focused_initial_pass_only` ersetzt.
- Die zugehörigen Detailtests verwenden katalogfreie Testnamen (`ZZRISK`,
  `ZZREGULAR`, `ZZBASE`, `ZZOTHER`) und prüfen weiterhin:
  - fokussierter Initial-Pass-only-Pfad,
  - regulärer Single-Base-Pfad mit einem Refinement-Pass,
  - Vorrang des expliziten Overrides,
  - Base-Name-Normalisierung,
  - Multi-Base-Default.

## 3) Nachweis

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_quality_pass_policy_helpers.py`
  → `5 passed`.
- `python tools/check_no_new_image_id_hardcoding.py`
  → `PASS: no image-ID hardcoding above legacy baseline (317 legacy occurrences remain).`

## 4) Ergebnis

IDO-17 baut die Legacy-Baseline weiter ab: Der Quality-Pass-Policy-Helfer und
sein direkter Aufrufer enthalten keine katalogspezifische Runtime-Risk-ID mehr;
der Ratchet sinkt von 322 auf 317 Runtime-ID-Vorkommen.

## 5) Nächster Schritt

IDO-17 fortsetzen und den nächsten verbleibenden katalogspezifischen Runtime-
Guard durch messbare Parameter, neutrale Metadaten oder reine Testdaten ersetzen.
