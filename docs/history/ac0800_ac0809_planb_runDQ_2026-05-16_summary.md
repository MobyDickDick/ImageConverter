# N2-PB Microbatch AC0800..AC0809 – Run DQ_PB (2026-05-16)

## Kontext
- **Anlass:** Gekoppelte Plan-B-Aufgabe zu N2 gemäß Kopplungsregel.

## Ausführung
- **Befehl:**
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 180 pyenv exec python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0800 --end AC0809 --deterministic-order`
- **Log-Artefakt:** `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-16_runDQ_PB.log`
- **Exit-Code:** `0`

## Ergebnis
Der gekoppelte Microbatch läuft reproduzierbar erfolgreich durch und bleibt damit als stabiler Plan-B-Nachweis nutzbar.
