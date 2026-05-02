# T5.16 Anchor-Debugprobe – 2026-05-02 (Run 01)

- **Ziel:** Weitere Debugdaten sammeln, warum die AC08-Blockierung trotz früherer Verbesserungen weiter besteht.
- **Befehl:**

```bash
set -o pipefail
timeout 420 python -m pytest   tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg   -vv -s --durations=0   | tee artifacts/converted_images/reports/T5_16_anchor_debug_2026-05-02_run01.log
```

## Beobachtungen aus dem Log

1. **Kein Rendering-Timeout / kein Render-Hänger**
   - Letzter Aggregate-Snapshot: `calls=475`, `slow_calls_gt_1s=0`, `timeouts=0`, `mean_elapsed=0.61s`.
2. **Blockierung verschiebt sich weg von MuPDF/Subprocess-Rendern**
   - Alle `render_probe`-Aufrufe im beobachteten Fenster liefern `status=done` und `returncode=0`.
3. **Auffälliger Wiederanlauf im AC0811-Block**
   - Sequenz enthält nach abgeschlossenem `AC0811_L` erneut `variant_start name=AC0811_S`.
   - Start-Events im Mitschnitt: `AC0811_S, AC0811_M, AC0811_L, AC0811_S, AC0811_M, AC0812_L, AC0812_S, AC0812_M`.
4. **Heartbeat-Daten zeigen Restbudget-Engstellen**
   - Wiederholt `HEARTBEAT` in `micro_search`/`element_loop`, u. a. mit niedrigem Restbudget kurz vor Folgerunden.

## Zwischenfazit

Die neuen Debugdaten sprechen gegen einen akuten Render-Subprozess-Hänger und deuten stärker auf **Steuerfluss-/Rundenlogik** im AC08-Anchor-Pfad hin (insbesondere Wiederanlauf von Varianten + Budgetverbrauch über mehrere Folgerunden).
