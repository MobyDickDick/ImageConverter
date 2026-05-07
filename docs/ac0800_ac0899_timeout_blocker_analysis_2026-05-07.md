# AC0800..AC0899 Timeout-Blockeranalyse (2026-05-07)

## Anlass
Nach dem Vollbereichs-Timeout in Run CD (`EXIT:124`) sollte der konkret verzögernde Teil identifiziert werden.

## Analyseweg
- Ausgewertet wurden die vorhandenen AC08-Element-Validierungslogs in `artifacts/converted_images/reports/*_element_validation.log`.
- Fokusmetriken:
  - Anzahl Validierungsrunden (`Runde N: elementweise Validierung gestartet`)
  - Kumulierte `global_search_elapsed`-Zeit aus `perf_probe`-Zeilen
  - Stagnationsmarker (`stagnation_detected`)
  - explizite `validation_time_budget_exceeded`-Marker

Verwendeter Auswertebefehl:

```bash
python - <<'PY'
from pathlib import Path
import re
root=Path('artifacts/converted_images/reports')
pat_round=re.compile(r'^Runde\s+(\d+): elementweise',re.M)
pat_perf=re.compile(r'perf_probe: global_search_elapsed round=\d+ elapsed=([0-9.]+)s')
rows=[]
for p in root.glob('AC08*_element_validation.log'):
    txt=p.read_text(errors='ignore')
    rounds=[int(x) for x in pat_round.findall(txt)]
    max_round=max(rounds) if rounds else 0
    g=[float(x) for x in pat_perf.findall(txt)]
    rows.append((sum(g),len(g),max_round,p.name,'stagnation_detected' in txt,'validation_time_budget_exceeded' in txt))
rows.sort(reverse=True)
for r in rows[:15]:
    print(r)
print('count',len(rows))
print('timeouts',sum(1 for r in rows if r[5]))
PY
```

## Ergebnis
1. **Kein einzelner Hänger/Deadlock** in den untersuchten AC08-Elementlogs: `validation_time_budget_exceeded` wurde dort in dieser Datenlage nicht gefunden.
2. Der **dominante Zeitverbrauch** entsteht wiederholt in der **globalen Parametersuche** (`global-search`) über viele Varianten (kumulativer Effekt), z. B.:
   - `AC0836_L_element_validation.log` (~3.37s globale Suche, 6 Runden)
   - `AC0838_M_element_validation.log` (~2.63s, 5 Runden, Stagnation)
   - `AC0831_L_element_validation.log` (~2.40s, 6 Runden, Stagnation)
3. Wiederkehrendes Muster: mehrere Runden + Stagnationsdetektion, aber trotzdem relevante Laufzeit bis zum Abbruch/Stop-Kriterium.

## Schlussfolgerung (Blocker)
Der Timeout in den 300s-Vollbereichsläufen wird **nicht** primär durch einen einzigen blockierten Variantenschritt verursacht, sondern durch die **Summe vieler teurer `global-search`-Runden** (inkl. Stagnationsrunden) über zahlreiche AC08-Varianten.

## Nächster technischer Hebel
- `global-search` im AC08-Kontext früher abbrechen bzw. aggressiver drosseln (z. B. weniger Samples/Runden bei erkennbarer Stagnation), um den Vollbereich in 300s zu halten.
