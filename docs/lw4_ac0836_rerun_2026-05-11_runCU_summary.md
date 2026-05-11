# LW4 – AC0836-Teil-Re-Run (Run CU) – 2026-05-11

- **Anlass:** Folgeschritt aus `docs/open_tasks.md`, um LW4 nach dem Exit-`139` in Run CT gezielt auf dem `AC0836`-Teilpfad zu vervollständigen.
- **Toolchain:** Python `3.10.20` via `pyenv` (`PYENV_VERSION=3.10.20`), `PYTHONPATH=vendor/linux-py310/site-packages`.

## Ausgeführter Befehl

`set -o pipefail; PYENV_VERSION=3.10.20 timeout 420 env PYTHONPATH=vendor/linux-py310/site-packages python -m src.imageCompositeConverter --start AC0836 --end AC0836 | tee artifacts/converted_images/reports/LW4_microbatch_2026-05-11_runCU_ac0836_py310.log`

## Ergebnis

- **Exit-Code:** `139`
- **Befund:** Der Re-Run reproduziert den bekannten Abbruch auf dem `AC0836`-Pfad (`MuPDF error: exception stack overflow!` mit nachgelagertem `Segmentation fault`).

## Kurzfazit

LW4 bleibt offen: Der gezielte Re-Run des zuvor fehlgeschlagenen AC0836-Teillaufs zeigt weiterhin keinen stabilen erfolgreichen Abschluss im Microbatch-Schema.
