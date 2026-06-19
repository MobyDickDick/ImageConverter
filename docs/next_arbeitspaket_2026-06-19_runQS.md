# Nächstes Arbeitspaket – IDO-17 Adaptive-Unlock-Entkopplung Run QS (2026-06-19)

## Ziel

Run QS startet nach IDO-16 das nächste dokumentierte Arbeitspaket aus
`docs/image_description_only_tasks.md`: IDO-17 reduziert verbleibende Runtime-
Katalog-IDs in `src/`. Als erster kleiner, prüfbarer Schritt wird die AC08-
Adaptive-Unlock-Auswahl von expliziten Familienlisten auf messbare Badge-
Merkmale umgestellt.

## Umsetzung

- `imageCompositeConverterSemanticAdaptiveLocks` prüft keine fest codierte
  Familienliste mehr, sondern aktiviert Phase 2 nur noch über den generischen
  Parameter `enable_adaptive_unlock`.
- Die Mindestfehlerschwelle kommt nun aus `adaptive_unlock_min_error` statt aus
  einer nach Katalogfamilien indizierten Map.
- `finalizeAc08StyleImpl(...)` leitet diese Parameter aus Textmodus und
  vorhandener Connector-Geometrie ab: VOC-Badges mit vertikalem Connector-Setup
  erhalten die bisherige höhere Schwelle; CO₂-Badges mit horizontalem Arm ohne
  Stem erhalten die kleinere Schwelle.
- Ein neuer neutraler Test mit katalogfremdem Namen `AC08XX_NEUTRAL` sichert ab,
  dass die Adaptive-Unlock-Eignung aus der Geometry-/Text-IR entsteht und nicht
  aus einer konkreten Bild-ID.
- Die Legacy-Ratchet-Baseline wurde nach der Entfernung der Adaptive-Unlock-
  Familienliste von 367 auf 362 Runtime-ID-Vorkommen abgesenkt.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/test_image_composite_converter.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/test_image_composite_converter.py::test_finalize_ac08_style_derives_adaptive_unlock_from_geometry_not_catalog_id tests/test_image_composite_converter.py::test_activate_ac08_adaptive_locks_supports_ac0882_family tests/test_image_composite_converter.py::test_validate_badge_by_elements_runs_ac0838_phase2_unlock_and_relock
```

Ergebnis: Exit `0`; der Ratchet meldet `362 legacy occurrences remain`, und der
gezielte Adaptive-Unlock-Testblock läuft mit `3 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Adaptive-Unlock-Regressionen.
- **Ergebnis:** Exit `0`; `3 passed`, Ratchet jetzt `362`.
- **Blocker:** IDO-17 ist noch nicht abgeschlossen; weitere Runtime-Katalog-IDs bleiben in anderen Spezialpfaden.
- **Dokumentation:** IDO-17 dokumentiert den ersten Baseline-Abbau und die geometriebasierte Adaptive-Unlock-Auswahl.
- **Nächster Schritt:** IDO-17 fortsetzen und die nächsten kleinen ID-spezifischen Runtime-Guards in struktur-/beschreibungsgesteuerte Parameter überführen.
