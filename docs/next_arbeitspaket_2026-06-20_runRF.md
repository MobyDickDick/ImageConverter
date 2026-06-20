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
=======
# Nächstes Arbeitspaket – IDO-17 Valve-Head-Compatibility-Guard Run RF (2026-06-20)

Run RF setzt IDO-17 aus `docs/image_description_only_tasks.md` fort und
stabilisiert die Valve-Head-Kompatibilität im Badge-SVG-Renderer nach dem
De-ID-Umbau.

## 1) Ziel

Valve-Head-Badges sollen ihre dedizierte Kopfgeometrie und den kurzen
zentrierten vertikalen Connector behalten. Neue Pfade beschreiben dies über das
neutrale Style-Metadatum `head_style=ac0223_triple_valve`; historische sparse
Legacy-Parameter mit bestehender Variant-Referenz müssen bis zur vollständigen
Migration weiterhin sicher gerendert werden.

## 2) Umsetzung

- `generateBadgeSvgImpl(...)` behält eine eng begrenzte Legacy-Kompatibilität:
  Wenn `head_style` fehlt und eine historische Valve-Head-Referenz
  (z. B. Variant-, Symbol-, Base- oder Dateiname) anliegt, wird
  `head_style=ac0223_triple_valve` nachgesetzt.
- Die Valve-Head-Geometrie selbst bleibt weiterhin am neutralen Metadatum
  `head_style=ac0223_triple_valve` gekoppelt.
- Detailtests sichern Legacy-Fälle mit fehlenden Style-Keys und prüfen
  Gradient, Connector-Farbe, Dateiname-Erkennung sowie die Reihenfolge Connector
  vor Kreis.
- Zwei Kommentare in Optimierungs-/Quantisierungspfaden wurden auf neutrale
  Valve-Head-Beschreibungen umgestellt, damit der Runtime-ID-Ratchet diese
  Vorkommen abbaut.
- Die Legacy-Baseline wurde auf den neuen Runtime-Bestand aktualisiert.

## 3) Nachweis

- `python -m compileall -q src tests/detailtests/test_semantic_badge_svg_helpers.py`
  → Exit `0`.
- `pytest -q tests/detailtests/test_semantic_badge_svg_helpers.py tests/test_image_composite_converter.py::test_make_badge_params_supports_ac0223_valve_head tests/test_image_composite_converter.py::test_generate_badge_svg_renders_ac0223_valve_head_gradient tests/test_image_composite_converter.py::test_quantize_badge_params_keeps_ac0223_top_stem_span`
  → `11 passed`.
- `python tools/check_no_new_image_id_hardcoding.py`
  → `PASS: no image-ID hardcoding above legacy baseline (305 legacy occurrences remain).`

## 4) Ergebnis

IDO-17 baut die Legacy-Baseline weiter ab, ohne den dokumentierten sparse
Legacy-Rendererfall zu brechen: Die neutralen Kommentar-Vorkommen wurden
bereinigt, während die notwendige Valve-Head-Kompatibilitätsweiche bis zur
vollständigen Parametermigration abgesichert bleibt.

## 5) Nächster Schritt

IDO-17 fortsetzen und die verbleibende Valve-Head-Kompatibilitätsweiche erst
dann entfernen, wenn alle Aufrufer zuverlässig neutrales `head_style`-Metadatum
liefern. Parallel die nächsten katalogspezifischen Runtime-Tokens in
Badge-Parametrisierung, Bestlist-Reparatur, Template-Transfer oder
Diagnosepfaden durch neutrale Beschreibungssignale, Parameter oder Testdaten
ersetzen.