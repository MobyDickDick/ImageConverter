# T5.7 – Isolierung des Langläufers im >96%-Testsegment (2026-04-27)

## Anlass

`docs/open_tasks.md` führt als offene Folgeaufgabe T5.7 die gezielte Isolierung
des Langläufers im Schlusssegment von `tests/test_image_composite_converter.py`
an, nachdem Gesamtläufe wiederholt bei `>96%` ohne Exit `0` hängen bzw. per
Timeout enden.

## Vorgehen

1. NodeIDs der Datei gesammelt:

   - `python -m pytest tests/test_image_composite_converter.py --collect-only -q > /tmp/tic_nodes.txt`

2. Schlusssegment (letzte 20 NodeIDs) extrahiert und als Probebereich definiert.
3. Reproduzierbare Einzeltest-Läufe mit hartem Zeitbudget gefahren:

   - `timeout 180 python -m pytest -q <nodeid>`

4. Ergebnisse inkl. Return-Code und Laufzeit in
   `artifacts/converted_images/reports/t5_7_probe_2026-04-27.txt` dokumentiert.

## Ergebnis

- Reproduzierbar isolierter Timeout-Kandidat:
  - `tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg`
  - Ergebnis als Einzeltest mit Zeitbudget `180s`: Exit `124`.
- Weitere auffällige, aber erfolgreiche Langläufer im selben Segment:
  - `...preserves_previously_good_variants[AC0820_L-semantic_ok]` (~82s)
  - `...preserves_previously_good_variants[AC0835_S-semantic_ok]` (~82s)
  - `...preserves_previously_good_variants[AC0837_L-semantic_ok]` (~86s)
  - `...test_ac0811_l_conversion_preserves_long_bottom_stem` (~68s)
  - `...test_ac0820_l_conversion_keeps_circle_diameter_above_half_image_width` (~70s)

## Einordnung

Die Aufgabe T5.7 ("Langläufer isolieren und zeitlich begrenzen") ist damit
erfüllt: Der blockierende Kandidat im Schlusssegment ist als eigener Root-Cause
reproduzierbar eingegrenzt und mit festem Timeout-Rahmen dokumentiert.
