# AC0811 Einzellauf – 2026-04-29 (Run BE)

- **Datum (UTC):** 2026-04-29
- **Anlass:** N7 (AC08-Zeitfehler) – bildspezifischer Diagnoselauf für `AC0811`.
- **Befehl:**

```bash
set -o pipefail
timeout 300 python -u -m src.imageCompositeConverter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir /tmp/imageconverter_runBE_AC0811 \
  --start AC0811 \
  --end AC0811 \
  --isolate-svg-render \
  --deterministic-order \
  | tee artifacts/converted_images/reports/AC0811_single_2026-04-29_runBE.log
```

- **Ausführung:** mit `tee` in `artifacts/converted_images/reports/AC0811_single_2026-04-29_runBE.log`
- **Sichtbarer Fortschritt im Log:** `AC0811_L.jpg` wurde gestartet.
- **Laufstatus:** Prozessende mit Exit-Code `0`; Variante `AC0811_L.jpg` lief in `TimeoutError: validation_time_budget_exceeded` (Runde 2, `elapsed=67.14s`, `budget=18.00s`).

## Kurzfazit

Der reproduzierbare Einzellauf für `AC0811` liegt vor und bestätigt weiterhin den dokumentierten Zeitbudget-Fehler im Element-Validierungspfad.
