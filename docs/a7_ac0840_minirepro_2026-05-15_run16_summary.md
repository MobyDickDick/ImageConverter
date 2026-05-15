# A7 Mini-Repro AC0840 (Follow-up) + gekoppelte Plan-B-Aufgabe – Run 16 (2026-05-15)

Direkte Fortsetzung der in `docs/open_tasks.md` dokumentierten A7-Nacharbeit: erneuter AC0840-Einzelpfad mit fixer Toolchain/Timeout plus gekoppelte Plan-B-Syntheseprobe.

## Primäraufgabe (A7): Mini-Repro nur AC0840

- **Befehl (Primärlauf):**
  - `PYENV_VERSION=3.10.20 timeout 180 python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0840 --end AC0840 --deterministic-order`
- **Log-Artefakt:** `artifacts/converted_images/reports/A7_AC0840_minirepro_2026-05-15_run16.log`
- **Exit-Code:** `0`
- **Befund:** Alle Varianten `AC0840_[L|M|S]` laufen erneut reproduzierbar in den Fallback-Modus und enden mit `conversion_failed`.

## Gekoppelte Plan-B-Aufgabe

- **Befehl (Plan B):**
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Grey circle with label rF" --variant AC0840_M`
- **Log-Artefakt:** `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-15_run16.log`
- **Exit-Code:** `0`
- **Befund:** Synthetische Probe liefert erneut `status=ok`.

## Kurzfazit

Der Real-Input-Pfad für `AC0840` bleibt stabil blockerhaft (`conversion_failed` über alle drei Varianten), während der gekoppelte Plan-B-Synthesepfad weiterhin erfolgreich ist. Damit verdichtet sich der Hinweis auf eine echte Differenz zwischen Real-Input- und synthetischem Input-Verhalten bei derselben Semantikklasse.
