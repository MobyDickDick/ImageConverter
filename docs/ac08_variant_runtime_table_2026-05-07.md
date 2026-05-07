# AC08 Laufzeittabelle je Bild (2026-05-07)

Gewünschte Übersicht „welches Bild wie lange zur Konvertierung benötigt“ wurde aus den vorhandenen
`*_element_validation.log`-Dateien erzeugt.

## Methodik

- Quelle: `artifacts/converted_images/reports/AC08*_element_validation.log`
- Messwert: Summe aller `perf_probe ... elapsed=...s`-Zeiten pro Variante.
- Wichtig: Das ist eine **Proxy-Laufzeit aus instrumentierten Teilphasen** (v. a. `global_search_elapsed`, `circle_center_elapsed`, `circle_radius_elapsed`) und nicht zwingend die komplette End-to-End-Wallclock pro Bild.

Vollständige Tabelle (108 Varianten) als CSV:
- `artifacts/converted_images/reports/ac08_variant_runtime_table_2026-05-07.csv`

## Top 20 nach gemessener `perf_probe_total_sec`

| Variante | Status | perf_probe_total_sec | global_search_sec | circle_center_sec | circle_radius_sec | probe_events |
|---|---:|---:|---:|---:|---:|---:|
| AC0836_L | semantic_ok | 3.55 | 3.37 | 0.08 | 0.10 | 18 |
| AC0838_M | semantic_ok | 2.98 | 2.63 | 0.25 | 0.10 | 11 |
| AC0831_L | semantic_ok | 2.74 | 2.40 | 0.16 | 0.18 | 16 |
| AC0870_M | semantic_ok | 2.08 | 1.66 | 0.35 | 0.07 | 14 |
| AC0835_L | semantic_ok | 2.07 | 1.87 | 0.11 | 0.09 | 18 |
| AC0882_M | semantic_ok | 1.99 | 1.36 | 0.50 | 0.13 | 18 |
| AC0842_L | semantic_ok | 1.79 | 1.27 | 0.35 | 0.17 | 7 |
| AC0881_M | semantic_ok | 1.72 | 1.25 | 0.37 | 0.10 | 18 |
| AC0838_L | semantic_ok | 1.66 | 1.62 | 0.04 | 0.00 | 10 |
| AC0820_S | semantic_ok | 1.31 | 0.97 | 0.27 | 0.07 | 10 |
| AC0842_M | semantic_ok | 1.30 | 1.08 | 0.15 | 0.07 | 7 |
| AC0882_L | semantic_ok | 1.23 | 0.93 | 0.23 | 0.07 | 7 |
| AC0837_L | semantic_ok | 1.01 | 0.79 | 0.13 | 0.09 | 10 |
| AC0833_L | semantic_ok | 0.87 | 0.82 | 0.05 | 0.00 | 11 |
| AC0814_S | semantic_ok | 0.86 | 0.64 | 0.16 | 0.06 | 10 |
| AC0832_M | semantic_ok | 0.84 | 0.66 | 0.13 | 0.05 | 10 |
| AC0820_L | semantic_ok | 0.79 | 0.57 | 0.19 | 0.03 | 14 |
| AC0831_M | semantic_ok | 0.75 | 0.70 | 0.02 | 0.03 | 18 |
| AC0811_L | semantic_ok | 0.69 | 0.54 | 0.13 | 0.02 | 10 |
| AC0839_M | semantic_ok | 0.57 | 0.46 | 0.06 | 0.05 | 7 |
