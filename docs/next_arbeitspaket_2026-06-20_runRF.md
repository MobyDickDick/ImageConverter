# Nächstes Arbeitspaket – IDO-17 Valve-Head-Runtime-Entkopplung Run RF (2026-06-20)

## Ziel

Run RF setzt IDO-17 aus `docs/image_description_only_tasks.md` als kleines,
prüfbares Folgepaket nach Run RE fort: Verbliebene AC0223-Runtime-Guards sollen
weiter aus dem produktiven Badge-Finalisierungs- und SVG-Rendering-Pfad entfernt
werden. Die Ventilkopf-Auswahl darf nicht mehr aus einem Katalognamen oder einer
Variantennamen-Präfixprüfung entstehen, sondern aus neutralen Style-Metadaten.

## Umsetzung

- `finalizeAc0223BadgeParamsImpl(...)` ist jetzt eine neutrale
  Ventilkopf-Finalisierung: Sie aktiviert den Pfad ausschließlich bei
  `head_style=ac0223_triple_valve` und ignoriert den übergebenen `base_name` als
  reine Aufruf-/Reporting-Metadaten.
- Der Badge-SVG-Renderer stellt den AC0223-Ventilkopf nicht länger aus
  `variant_name`/`badge_symbol_name`/`base_name` wieder her. Sparse Legacy-Caller
  müssen den neutralen `head_style`-Parameter liefern; der Renderer entscheidet
  damit nicht mehr anhand eines Katalog-ID-Präfixes.
- Der Runtime-Helper-Test verwendet einen neutralen Dateistamm
  `ZZ_NEUTRAL_VALVE` und sichert, dass Ventilkopf-Geometrie allein über
  `head_style=ac0223_triple_valve` finalisiert wird.
- Die Legacy-Ratchet-Baseline wurde nach dem Entfernen der beiden AC0223-
  Runtime-Guards von 307 auf 305 Runtime-ID-Vorkommen abgesenkt.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_ac0223_runtime_helpers.py tests/test_image_composite_converter.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_ac0223_runtime_helpers.py tests/test_image_composite_converter.py::test_make_badge_params_supports_ac0223_valve_head tests/test_image_composite_converter.py::test_generate_badge_svg_renders_ac0223_valve_head_gradient
```

Ergebnis: Exit `0`; der Ratchet meldet `305 legacy occurrences remain`, und der
gezielte Ventilkopf-Testblock läuft mit `4 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte AC0223-/neutrale Ventilkopf-Regressionen.
- **Ergebnis:** Exit `0`; `4 passed`, Ratchet jetzt `305`.
- **Blocker:** IDO-17 ist noch nicht abgeschlossen; weitere Runtime-Katalog-IDs bleiben in anderen Spezialpfaden.
- **Dokumentation:** IDO-17 dokumentiert einen weiteren Baseline-Abbau und die Style-Metadaten-basierte Ventilkopf-Finalisierung.
- **Nächster Schritt:** IDO-17 fortsetzen und weitere ID-spezifische Runtime-Guards in struktur-/beschreibungsgesteuerte Parameter überführen.
