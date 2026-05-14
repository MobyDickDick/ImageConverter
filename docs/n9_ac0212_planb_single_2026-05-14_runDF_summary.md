# N9 – Plan-B-Einzelprobe AC0212 (Run DF, 2026-05-14)

- **Datum:** 2026-05-14
- **Primäraufgabe (N9):** Isolierter Kurzlauf für `AC0212` mit dokumentiertem Repro-Befehl.
- **Befehl (Primärlauf):**

```bash
set -o pipefail; PYENV_VERSION=3.10.20 timeout 300 python -u -m src.imageCompositeConverter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --start AC0212 \
  --end AC0212 \
  --isolate-svg-render \
  --deterministic-order \
  | tee artifacts/converted_images/reports/AC0212_single_planbprobe_2026-05-14_runDF.log
```

- **Exit-Code (Primärlauf):** `0`
- **Log-Artefakt (Primärlauf):** `artifacts/converted_images/reports/AC0212_single_planbprobe_2026-05-14_runDF.log`

## Gekoppelte Plan-B-Aufgabe (Run DF_PB)

- **Plan-B-Ziel:** synthetischer Einzelfall-Repro für `AC0212_L` (Beschreibung → SVG → JPG → Konvertierung), um bei künftigen Blockern sofort auf einen kleineren Scope zu rotieren.
- **Befehl (Plan B):**

```bash
set -o pipefail; PYENV_VERSION=3.10.20 timeout 180 python tools/plan_b_synthetic_probe.py \
  "2-Weg Ventil vertikal mit Kreis rechts, horizontalem Griff und Buchstabe M im Kreis." \
  --variant AC0212_L \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  | tee artifacts/converted_images/reports/AC0212_planb_synthetic_2026-05-14_runDF_PB.log
```

- **Exit-Code (Plan B):** `0`
- **Log-Artefakt (Plan B):** `artifacts/converted_images/reports/AC0212_planb_synthetic_2026-05-14_runDF_PB.log`

## Kurzfazit

N9 ist damit inklusive reproduzierbarem Kurzlaufbefehl und Summary-Datei umgesetzt. Die gekoppelte Plan-B-Aufgabe wurde im selben Lauf dokumentiert und ebenfalls mit Exit `0` abgeschlossen.
