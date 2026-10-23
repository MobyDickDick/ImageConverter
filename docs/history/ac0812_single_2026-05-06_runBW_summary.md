# AC0812 Einzellauf – 2026-05-06 (Run BW)

- **Datum (UTC):** 2026-05-06
- **Anlass:** N7 (AC08-Zeitfehler) – bildspezifischer Diagnoselauf für `AC0812`.
- **Befehl:**

```bash
set -o pipefail
timeout 300 python -u -m src.imageCompositeConverter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir /tmp/imageconverter_runBW_AC0812 \
  --start AC0812 \
  --end AC0812 \
  --isolate-svg-render \
  --deterministic-order \
  | tee artifacts/converted_images/reports/AC0812_single_2026-05-06_runBW.log
```

- **Ausführung:** mit `tee` in `artifacts/converted_images/reports/AC0812_single_2026-05-06_runBW.log`
- **Sichtbarer Fortschritt im Log:** Kein Variantenfortschritt; nur der bekannte Hinweis `OpenCV bindings requires "numpy" package` plus Abschlussmeldung.
- **Laufstatus:** Prozessende mit Exit-Code `0`, aber ohne belastbaren AC0812-Diagnosefortschritt.

## Kurzfazit

Der N7-Einzellauf für `AC0812` wurde formal ausgeführt und dokumentiert, ist aber inhaltlich durch die aktuell fehlende/inkompatible `numpy`-Laufzeitumgebung blockiert. Für die N7-Abnahme wird ein Folge-Lauf mit tatsächlich sichtbarem Variantenfortschritt benötigt.
