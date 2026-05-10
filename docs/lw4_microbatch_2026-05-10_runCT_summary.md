# LW4 – 3er-Microbatch-Probe (Run CT) – 2026-05-10

- **Anlass:** Abarbeitung der nächsten offenen Aufgabe aus `docs/open_tasks.md` (LW4).
- **Toolchain:** Python `3.10.20` via `pyenv`, `PYTHONPATH=vendor/linux-py310/site-packages`.
- **Zielscope:** `AC0836_L`, `AC0838_M`, `AC0831_L` als schneller N1/N2-Proxy.

## Ausgeführte Befehle

1. `timeout 420 env PYTHONPATH=vendor/linux-py310/site-packages python -m src.imageCompositeConverter --start AC0836 --end AC0836 | tee artifacts/converted_images/reports/LW4_microbatch_2026-05-10_runCT_ac0836.log`
2. `timeout 420 env PYTHONPATH=vendor/linux-py310/site-packages python -m src.imageCompositeConverter --start AC0838 --end AC0838 | tee artifacts/converted_images/reports/LW4_microbatch_2026-05-10_runCT_ac0838.log`
3. `timeout 420 env PYTHONPATH=vendor/linux-py310/site-packages python -m src.imageCompositeConverter --start AC0831 --end AC0831 | tee artifacts/converted_images/reports/LW4_microbatch_2026-05-10_runCT_ac0831.log`

## Ergebnis

| Teilprobe | Exit-Code | Ergebnis |
|---|---:|---|
| AC0836 | 139 | Abbruch mit `MuPDF error: exception stack overflow!` |
| AC0838 | 0 | Erfolgreich abgeschlossen |
| AC0831 | 0 | Erfolgreich abgeschlossen |

## Kurzfazit

LW4 ist **teilweise** ausgeführt, aber noch nicht abgeschlossen: zwei von drei Mikrobatch-Teilläufen sind stabil (`AC0838`, `AC0831`), während `AC0836` in diesem Lauf mit Exit `139` abgebrochen ist. Vor dem Setzen von LW4 auf erledigt ist ein reproduzierbarer, erfolgreicher AC0836-Teillauf im selben Microbatch-Schema erforderlich.
