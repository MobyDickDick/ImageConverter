# T5.16 Steuerfluss-Diagnose – 2026-05-02 (Run 02)

## Ziel
Die Ursache für den erneuten Variantenstart (z. B. nach AC0811_L wieder AC0811_S/M) eindeutig einer Queue-/Retry-Quelle zuordnen.

## Umgesetzte Instrumentierung
- `convertOneImpl` ergänzt `variant_start`/`variant_done` im Anchor-Test um ein neues Feld `context=...`.
- Initial-Pass setzt `context=initial_pass:<idx>/<total>`.
- Quality-Pass setzt `context=quality_pass:<pass>;candidate=<variant>;candidates=<n>`.

## Repro-Lauf
```bash
set -o pipefail
timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0   | tee artifacts/converted_images/reports/T5_16_anchor_debug_2026-05-02_run02.log
```

## Ergebnis (eindeutige Quelle)
Extrahierte `variant_start`-Kontexte aus Run 02:
- `AC0811_S` → `initial_pass:1/3`
- `AC0811_L` → `initial_pass:2/3`
- `AC0811_M` → `initial_pass:3/3`
- `AC0811_M` → `quality_pass:1;candidate=AC0811_M;candidates=2`

**Interpretation:**
Der Wiederanlauf kommt nicht aus einer „versteckten Endlosschleife“ im Initial-Pass, sondern aus dem **bewusst folgenden Quality-Pass-Reprocessing**. Die beobachteten Re-Starts sind damit als zweite Pipeline-Phase identifiziert.
