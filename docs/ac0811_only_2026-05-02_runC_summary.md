# AC0811-Only Lauf – Vorher/Nachher nach Quality-Pass-Fast-Path (2026-05-02 Run C)

## Ziel
Weitere Reduktion von Laufzeit und Wiederholungen im AC0811-Only-Scope mit minimalem Eingriff.

## Code-Änderung
Für Single-Base-Runs wird die Zahl globaler Quality-Passes standardmäßig von `4` auf `1` reduziert (overridebar via `ICC_MAX_QUALITY_PASSES`).

## Repro-Befehl
```bash
python - <<'PY' 2>&1 | tee artifacts/converted_images/reports/AC0811_only_2026-05-02_runC.log
import subprocess, time
cmd=['python','-u','-m','src.imageCompositeConverter','artifacts/images_to_convert','--descriptions-path','artifacts/images_to_convert/Finale_Wurzelformen_V3.xml','--output-dir','/tmp/imageconverter_ac0811_probe3','--start','AC0811','--end','AC0811','--isolate-svg-render','--deterministic-order']
start=time.monotonic(); proc=subprocess.run(cmd, text=True, capture_output=True); end=time.monotonic()
print(proc.stdout, end=''); print(proc.stderr, end='')
print(f'RUN_METRIC elapsed_sec={end-start:.2f} returncode={proc.returncode}')
PY
```

## Vorher/Nachher
- **Run B (vorher):** `elapsed_sec=395.59`, Exit `0`, kein `validation_time_budget_exceeded`.
- **Run C (nachher):** `elapsed_sec=363.78`, Exit `0`, kein `validation_time_budget_exceeded`.
- **Delta:** `-31.81s` (~`8.0%` schneller).
- **Wiederholungen:** weiterhin vorhanden, aber reduziert (M/S weniger Repeats als in Run B).

## Fazit
Mit sehr kleinem Eingriff wurde die Konvergenzzeit messbar verbessert, ohne Timeout-Rückfall und ohne semantische Sonderlogik im AC0811-Pfad selbst.
