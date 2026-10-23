# LW3 – AC0831_L Isolation (Run CS1–CS3) – 2026-05-10

- **Anlass:** Abarbeitung der nächsten offenen Aufgabe aus `docs/open_tasks.md` (LW3).
- **Toolchain:** Python `3.10.20` via `pyenv`, `PYTHONPATH=vendor/linux-py310/site-packages`.
- **Befehl (pro Wiederholung):** `timeout 420 env PYTHONPATH=vendor/linux-py310/site-packages python -m src.imageCompositeConverter --start AC0831 --end AC0831`
- **Konsolen-Logs:**
  - `artifacts/converted_images/reports/LW3_ac0831L_isolation_2026-05-10_runCS1_py310.log`
  - `artifacts/converted_images/reports/LW3_ac0831L_isolation_2026-05-10_runCS2_py310.log`
  - `artifacts/converted_images/reports/LW3_ac0831L_isolation_2026-05-10_runCS3_py310.log`
- **Gesicherte Element-Logs pro Wiederholung:**
  - `artifacts/converted_images/reports/AC0831_L_element_validation_runCS1.log`
  - `artifacts/converted_images/reports/AC0831_L_element_validation_runCS2.log`
  - `artifacts/converted_images/reports/AC0831_L_element_validation_runCS3.log`

## Messergebnisse (kumulierte `global_search_elapsed` für `AC0831_L`)

| Wiederholung | Exit-Code | Samples | Stagnation | kum. global-search [s] |
|---|---:|---:|---:|---:|
| CS1 | 0 | 6 | ja | 2.40 |
| CS2 | 0 | 6 | ja | 2.40 |
| CS3 | 0 | 6 | ja | 2.40 |

### Aggregat (3 Wiederholungen)

- **min:** `2.40s`
- **median:** `2.40s`
- **max:** `2.40s`

## Kurzfazit

LW3 ist erfüllt: `AC0831_L` wurde dreifach isoliert reproduziert, und das Schwankungsband der kumulierten global-search-Zeit ist in diesem Setup `0.00s` (vollständig stabil bei `2.40s`).
