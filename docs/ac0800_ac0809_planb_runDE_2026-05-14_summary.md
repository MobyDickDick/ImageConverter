# AC0800..AC0809 Plan-B-Microbatch – Run DE_PB (2026-05-14)

- **Datum:** 2026-05-14
- **Run-ID:** DE_PB
- **Befehl:** `set -o pipefail; PYENV_VERSION=3.10.20 timeout 420 python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0800 --end AC0809 | tee artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDE_PB.log`
- **Exit-Code:** `0`
- **Log-Artefakt:** `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDE_PB.log`

## Kurzfazit
Die gekoppelte Plan-B-Aufgabe wurde direkt nach dem N1-Timeout ausgeführt. Der reduzierte Microbatch (`AC0800..AC0809`) lief mit denselben Runtime-Parametern erfolgreich durch und liefert einen stabilen Kurzlauf-Nachweis mit Exit `0`.
