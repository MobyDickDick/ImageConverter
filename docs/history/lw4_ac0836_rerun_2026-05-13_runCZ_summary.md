# LW4 – AC0836-Teil-Re-Run (Run CZ) – 2026-05-13

- **Anlass:** Nächster offener LW4-Schritt aus `docs/open_tasks.md`: AC0836 als verbleibenden Microbatch-Rest erneut mit identischer Toolchain prüfen.
- **Toolchain:** Python `3.10.20` via `pyenv` (`PYENV_VERSION=3.10.20`), `PYTHONPATH=vendor/linux-py310/site-packages`.

## Ausgeführter Befehl

`set -o pipefail; PYENV_VERSION=3.10.20 timeout 420 env PYTHONPATH=vendor/linux-py310/site-packages python -m src.imageCompositeConverter --start AC0836 --end AC0836 | tee artifacts/converted_images/reports/LW4_microbatch_2026-05-13_runCZ_ac0836_py310.log`

## Ergebnis

- **Exit-Code:** `0`
- **Befund:** Der isolierte AC0836-Microbatch-Lauf lief stabil durch (`AC0836_S`, `AC0836_L`, `AC0836_M`) und erzeugte reguläre Report-Artefakte ohne Segfault/Stack-Overflow.

## Kurzfazit

LW4 ist damit abgeschlossen: Der zuvor offene AC0836-Microbatch-Rest wurde mit Exit `0` erfolgreich dokumentiert.
