# Nächstes Arbeitspaket – IDO-17 Small-Circle-Fallback-Entkopplung Run QT (2026-06-19)

## Ziel

Run QT setzt das nächste kleine IDO-17-Paket aus
`docs/image_description_only_tasks.md` fort: Weitere Runtime-Katalog-IDs werden
aus `src/` entfernt. Konkret wird der AC08-Small-Circle-Rescue-Pfad in der
semantischen Primitive-Erkennung von einer expliziten Familienliste auf
messbare beziehungsweise bereits abgeleitete Badge-Eigenschaften umgestellt.

## Umsetzung

- `imageCompositeConverterSemanticChecks` enthält keine
  `AC08_SMALL_CIRCLE_FALLBACK_FAMILIES`-Allowlist mehr.
- Der Small-Circle-Rescue-Pfad wird nur noch aktiviert, wenn
  `ac08_small_variant_mode` gesetzt ist, die Kreisgeometrie nicht deaktiviert
  wurde und eine endliche erwartete Kreis-Schätzung (`cx`, `cy`, `r`) vorliegt.
- Die Diagnosequelle heißt nun `geometry_fallback`, damit der Report nicht mehr
  suggeriert, dass eine Katalogfamilie die Entscheidung getroffen hat.
- Ein neuer synthetischer Test mit dem katalogfremden Namen
  `NEUTRAL_SMALL_RING` sichert, dass der Fallback ohne Bild-ID aus
  Geometrieparametern funktioniert.
- Die Legacy-Ratchet-Baseline wurde nach Entfernung der Small-Circle-
  Familienliste von 360 auf 335 Runtime-ID-Vorkommen abgesenkt.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/test_image_composite_converter.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/test_image_composite_converter.py::test_detect_semantic_primitives_small_circle_fallback_is_catalog_name_free tests/test_image_composite_converter.py::test_detect_semantic_primitives_reports_small_circle_geometry_fallback_source
```

Ergebnis: Exit `0`; der Ratchet meldet `335 legacy occurrences remain`, und der
gezielte Small-Circle-Fallback-Testblock läuft mit `4 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Small-Circle-Fallback-Regressionen.
- **Ergebnis:** Exit `0`; `4 passed`, Ratchet jetzt `335`.
- **Blocker:** IDO-17 ist noch nicht abgeschlossen; weitere Runtime-Katalog-IDs bleiben in anderen Spezialpfaden.
- **Dokumentation:** IDO-17 dokumentiert den weiteren Baseline-Abbau und die geometriebasierte Small-Circle-Fallback-Auswahl.
- **Nächster Schritt:** IDO-17 fortsetzen und weitere ID-spezifische Runtime-Guards in struktur-/beschreibungsgesteuerte Parameter überführen.
