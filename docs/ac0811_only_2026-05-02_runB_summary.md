# AC0811-Only Lauf (ohne explizites Zeitlimit) – 2026-05-02 Run B

- **Datum (UTC):** 2026-05-02
- **Anlass:** gezielter Folge-Lauf nach Umstellung auf element-first-Validierung und Wegfall impliziter Default-Zeitlimits.
- **Befehl:**

```bash
python - <<'PY' 2>&1 | tee artifacts/converted_images/reports/AC0811_only_2026-05-02_runB.log
import subprocess, time
cmd=['python','-u','-m','src.imageCompositeConverter','artifacts/images_to_convert','--descriptions-path','artifacts/images_to_convert/Finale_Wurzelformen_V3.xml','--output-dir','/tmp/imageconverter_ac0811_probe2','--start','AC0811','--end','AC0811','--isolate-svg-render','--deterministic-order']
start=time.monotonic()
proc=subprocess.run(cmd, text=True, capture_output=True)
end=time.monotonic()
print(proc.stdout, end='')
print(proc.stderr, end='')
print(f'RUN_METRIC elapsed_sec={end-start:.2f} returncode={proc.returncode}')
PY
```

## Ergebnis

- **Exit-Code:** `0`
- **Gemessene Laufzeit:** `RUN_METRIC elapsed_sec=395.59`
- **Timeout-Marker:** kein `validation_time_budget_exceeded` im Lauf-Log.
- **Beobachtung zum Ablauf:** der Lauf endet erfolgreich, zeigt aber wiederholte Verarbeitung von `AC0811_M` und `AC0811_S` (mehrfaches Auftreten im Konsolenlog).

## Kurzfazit

- Positiv: Lauf ist ohne explizites `timeout` sauber abgeschlossen und ohne Budget-Timeout-Marker.
- Offener Punkt: Die wiederholte M/S-Verarbeitung deutet auf einen verbleibenden Kontrollfluss-/Queue-Effekt im AC0811-Pfad hin und sollte als nächstes gezielt analysiert werden.
