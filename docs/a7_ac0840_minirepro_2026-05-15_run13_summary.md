# A7 Mini-Repro AC0840 + gekoppelte Plan-B-Aufgabe – Run 13 (2026-05-15)

## Anlass
Abarbeitung des in `docs/open_tasks.md` als nächster Schritt genannten A7-Mini-Repros für `AC0840` (Input-/Semantikpfad prüfen) inklusive gekoppelter Plan-B-Aufgabe.

## Primäraufgabe (A7): Mini-Repro nur AC0840
- **Befehl:**
  - `PYENV_VERSION=3.10.20 timeout 180 python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0840 --end AC0840 --deterministic-order`
- **Log-Artefakt:** `artifacts/converted_images/reports/A7_AC0840_minirepro_2026-05-15_run13.log`
- **Exit-Code:** `0`
- **Befund:** Alle drei Varianten `AC0840_[L|M|S]` laufen in den Fallback-Modus und enden jeweils mit `conversion_failed`.

## Gekoppelte Plan-B-Aufgabe
- **Befehl:**
  - `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Grey circle with label rF" --variant AC0840_L`
- **Log-Artefakt:** `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-15_run13.log`
- **Exit-Code:** `0`
- **Befund:** Synthetische Probe liefert `status=ok` für `AC0840_L`.

## Kurzfazit
Der A7-Repro bestätigt den Blocker als variantenübergreifend im Real-Input-Pfad (`AC0840_[L|M|S]`), während der gekoppelte Plan-B-Synthesepfad weiterhin grün ist. Nächster sinnvoller Schritt ist damit ein gezielter Vergleich Real-Input vs. synthetischer Input auf derselben Formklasse (Label-/Textanteil) vor einem erneuten Blocklauf.
