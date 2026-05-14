# N1-Plan-B Microbatch AC0800..AC0809 – Run DC_PB (2026-05-14)

- **Datum:** 2026-05-14
- **Run-ID:** DC_PB
- **Befehl:** `set -o pipefail; PYENV_VERSION=3.10.20 timeout 420 python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0800 --end AC0809 | tee artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDC_PB.log`
- **Exit-Code:** `0`
- **Log-Artefakt:** `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDC_PB.log`

## Kurzfazit
Gemäß N1-PB-Kopplungsregel wurde nach dem N1-Timeout direkt der gekoppelte 10-Varianten-Microbatch ausgeführt. Der Lauf endete mit Exit `0`; im Log ist sichtbarer Fortschritt bis zu den verarbeiteten `AC0800_*`-Varianten dokumentiert.
