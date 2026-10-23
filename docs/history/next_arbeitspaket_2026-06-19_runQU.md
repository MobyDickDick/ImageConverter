# Nächstes Arbeitspaket – IDO-17 Plain-Ring-Entkopplung Run QU (2026-06-19)

## Ziel

Run QU setzt IDO-17 aus `docs/image_description_only_tasks.md` als kleines,
prüfbares Folgepaket nach Run QT fort: Weitere Runtime-Katalog-IDs sollen aus
`src/` entfernt werden. Konkret wird die Plain-Ring-Erhaltung für AC08-Badges
nicht mehr über den Katalognamen im Finalisierungs- und SVG-Pfad erkannt,
sondern über ein explizites, bereits abgeleitetes Geometrie-Merkmal.

## Umsetzung

- Der AC08-Parameteraufbau markiert Plain-Ring-Badges mit
  `preserve_plain_ring_geometry`.
- `finalizeAc08StyleImpl(...)` nutzt dieses Geometrie-Merkmal statt eines
  `AC0800`-Namensvergleichs, um Radius-/Center-Locks und die Edge-Ring-
  Reankerung anzuwenden.
- Der Badge-SVG-Renderer aktiviert den zusätzlichen Plain-Ring-Marker über
  `plain_ring_geometry` statt über Variantennamen oder `badge_symbol_name`.
- Ein neuer neutraler Test mit `AC08XX_RING` sichert, dass die Plain-Ring-
  Erhaltung aus Parametern und nicht aus einer konkreten Katalog-ID entsteht.
- Die Legacy-Ratchet-Baseline wurde nach der Entfernung der Plain-Ring-
  Namensguards von 335 auf 331 Runtime-ID-Vorkommen abgesenkt.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/test_image_composite_converter.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/test_image_composite_converter.py::test_finalize_ac0800_preserves_plain_ring_geometry_bounds tests/test_image_composite_converter.py::test_finalize_plain_ring_geometry_uses_parameter_not_catalog_id tests/test_image_composite_converter.py::test_parse_description_marks_ac0800_as_plain_ring_family
```

Ergebnis: Exit `0`; der Ratchet meldet `331 legacy occurrences remain`, und der
gezielte Plain-Ring-Testblock läuft mit `5 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Plain-Ring-Regressionen.
- **Ergebnis:** Exit `0`; `5 passed`, Ratchet jetzt `331`.
- **Blocker:** IDO-17 ist noch nicht abgeschlossen; weitere Runtime-Katalog-IDs bleiben in anderen Spezialpfaden.
- **Dokumentation:** IDO-17 dokumentiert einen weiteren Baseline-Abbau und die parameterbasierte Plain-Ring-Erhaltung.
- **Nächster Schritt:** IDO-17 fortsetzen und weitere ID-spezifische Runtime-Guards in struktur-/beschreibungsgesteuerte Parameter überführen.
