# AC08 begrenzende Faktoren – Bildweise Laufzeitindikatoren (Stand: 2026-05-09)

## Fragestellung
Welche Bilder wirken aktuell als Laufzeitbremse, und wie lange dauern deren aufwändige Teilschritte?

## Methode
Aus den vorhandenen `AC08*_element_validation.log`-Dateien wurden pro Bild folgende Indikatoren extrahiert:

- kumulierte Dauer der globalen Suche (`perf_probe: global_search_elapsed ... elapsed=...s`)
- Anzahl global-search-Samples
- maximale Validierungsrunde
- Stagnationsmarker (`stagnation_detected`)

Auswertekommando:

```bash
python - <<'PY'
from pathlib import Path
import re
root=Path('artifacts/converted_images/reports')
pat_round=re.compile(r'^Runde\s+(\d+): elementweise',re.M)
pat_perf=re.compile(r'perf_probe: global_search_elapsed round=\d+ elapsed=([0-9.]+)s')
rows=[]
for p in sorted(root.glob('AC08*_element_validation.log')):
    txt=p.read_text(errors='ignore')
    rounds=[int(x) for x in pat_round.findall(txt)]
    max_round=max(rounds) if rounds else 0
    g=[float(x) for x in pat_perf.findall(txt)]
    rows.append((p.name,sum(g),len(g),max_round,'stagnation_detected' in txt,'validation_time_budget_exceeded' in txt))
rows=[r for r in rows if r[2]>0]
rows.sort(key=lambda r:r[1], reverse=True)
for r in rows[:12]:
    print(r)
PY
```

## Top-Begrenzungsfaktoren (global-search kumuliert)

| Rang | Bild (Log) | kum. global-search [s] | Samples | max Runde | Stagnation |
|---|---|---:|---:|---:|---:|
| 1 | `AC0836_L_element_validation.log` | 3.370 | 6 | 6 | nein |
| 2 | `AC0838_M_element_validation.log` | 2.630 | 5 | 5 | ja |
| 3 | `AC0831_L_element_validation.log` | 2.400 | 6 | 6 | ja |
| 4 | `AC0835_L_element_validation.log` | 1.870 | 6 | 6 | nein |
| 5 | `AC0870_M_element_validation.log` | 1.660 | 6 | 6 | ja |
| 6 | `AC0838_L_element_validation.log` | 1.620 | 6 | 6 | ja |
| 7 | `AC0882_M_element_validation.log` | 1.360 | 6 | 6 | nein |
| 8 | `AC0842_L_element_validation.log` | 1.270 | 3 | 3 | ja |
| 9 | `AC0881_M_element_validation.log` | 1.250 | 6 | 6 | nein |
| 10 | `AC0842_M_element_validation.log` | 1.080 | 3 | 3 | ja |

## Interpretation
- Der Engpass ist **kumulativ**: mehrere Varianten mit 1–3s global-search summieren sich über den Vollbereich.
- Besonders auffällig sind Varianten mit **hohen Rundenzahlen (5–6)** plus Stagnation.
- In dieser Datenlage taucht in den untersuchten Element-Logs kein expliziter `validation_time_budget_exceeded`-Marker auf; der Vollbereich scheitert weiterhin über den äußeren Timeout.

## Daraus abgeleitete leichtgewichtige Aufgaben (für nächste Sessions)
1. **LW1 – AC0836_L isoliert messen**
   - Ziel: Reproduzierbar die 6 Runden + ~3.37s global-search verifizieren.
   - Repro: nur `AC0836_L` konvertieren, Element-Log sichern.
2. **LW2 – AC0838_M Stagnationspfad prüfen**
   - Ziel: Stagnationspunkt dokumentieren (ab welcher Runde) und Laufzeit pro Runde tabellieren.
3. **LW3 – AC0831_L mit identischer Toolchain gegenmessen**
   - Ziel: Stabilität der ~2.40s bestätigen und Schwankungsband erfassen (min/median/max aus 3 Läufen).
4. **LW4 – 3er-Microbatch (`AC0836_L`, `AC0838_M`, `AC0831_L`)**
   - Ziel: schneller Proxy für N1/N2-Fortschritt ohne Vollbereich, inkl. Summenlaufzeitvergleich.
