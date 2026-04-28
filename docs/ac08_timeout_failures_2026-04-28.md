# AC08-Zeitfehler aus `python -m pytest` (Stand 2026-04-28)

Diese Liste dokumentiert die Tests aus dem Volltestlauf vom 2026-04-28, die mit
`validation_time_budget_exceeded` (direkt oder Folgefehler) aufgefallen sind.
Ziel ist eine gezielte Einzel-Konvertierung der betroffenen Varianten.

## Fehlgeschlagene Tests mit Zeitbezug

| Testname | Zeitfehler-Typ | Betroffene Variante(n)/Bild(er) |
|---|---|---|
| `tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius` | direktes `TimeoutError` in Badge-Validierung | `AC0812_S.jpg` |
| `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout` | direktes `TimeoutError` in Badge-Validierung | `AC0838_M.jpg` |
| `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation` | direktes `TimeoutError` in Badge-Validierung | synthetischer AC08-Fall (`AC0831`-Parameter) |
| `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]` | `TimeoutError` innerhalb Pipeline-Lauf | `AC0820_L.jpg` |
| `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]` | `TimeoutError` innerhalb Pipeline-Lauf | `AC0835_S.jpg` |
| `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok]` | `TimeoutError` innerhalb Pipeline-Lauf | `AC0837_L.jpg` |
| `tests/test_image_composite_converter.py::test_ac0811_l_conversion_preserves_long_bottom_stem` | Folgefehler (`FileNotFoundError`) nach vorgeschaltetem `TimeoutError` | `AC0811_L.jpg` |
| `tests/test_image_composite_converter.py::test_ac0820_l_conversion_keeps_circle_diameter_above_half_image_width` | `TimeoutError` innerhalb Pipeline-Lauf | `AC0820_L.jpg` |
| `tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg` | Folgefehler (`AssertionError`) nach vorgeschaltetem `TimeoutError` | primär `AC0811_L.jpg` (Test enthält zusätzlich `AC0812_M`) |

## Zielgerichtete Konvertierung der betroffenen Bilder

Für einen schnellen Repro-/Diagnoselauf pro Variante kann jeweils nur die
betroffene Referenz konvertiert werden:

```bash
python -m src.imageCompositeConverter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir /tmp/imageconverter_targeted \
  --start <REF> \
  --end <REF> \
  --isolate-svg-render \
  --deterministic-order
```

Empfohlene `<REF>`-Liste aus den Zeitfehlern:

- `AC0811`
- `AC0812`
- `AC0820`
- `AC0835`
- `AC0837`
- `AC0838`

Hinweis: Für den synthetischen Testfall (`AC0831`-Parameter) gibt es kein
1:1-JPEG-Fixture als direkte Einzeldatei; dieser Fall wird über den Test selbst
reproduziert.
