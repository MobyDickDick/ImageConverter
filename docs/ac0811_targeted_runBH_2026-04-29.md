# AC0811 Targeted Run BH (2026-04-29)

- Anlass: N7-Diagnoselauf für AC08-Zeitfehler (`AC0811` als Einzelreferenz).
- Befehl:
  `timeout 300 python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/imageconverter_targeted --start AC0811 --end AC0811 --isolate-svg-render --deterministic-order`
- Log: `artifacts/converted_images/reports/AC0811_targeted_2026-04-29_runBH.log`
- Beobachtung: Lauf endete mit Shell-Exit `0`, enthält aber für `AC0811_L.jpg` weiterhin `TimeoutError: validation_time_budget_exceeded` (Round-Start Runde 2, `elapsed=63.44s`, `budget=18.00s`).
- Kurzfazit: Zeitfehler für `AC0811` ist im gezielten Einzel-Run reproduzierbar und als N7-Befund dokumentiert.
