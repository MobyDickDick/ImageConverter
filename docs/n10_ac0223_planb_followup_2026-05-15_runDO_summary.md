# N10-Follow-up – AC0223 Plan-B + T5-Kurzlauf (Run DO, 2026-05-15)

## Ziel
- Den in `docs/open_tasks.md` als nächsten Schritt benannten Plan-B-Pfad **N10-PB** für `AC0223` ausführen.
- Zusätzlich einen weiteren priorisierten Kurzlauf aus dem leichten Pfad (**T5.x**) mit reproduzierbarem Exit-Code dokumentieren.

## Ausführung

### 1) Plan-B-Aufgabe (N10-PB)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 180 pyenv exec python -m tools.plan_b_synthetic_probe --variant AC0223 "Kelle mit links liegendem Griff und Label rF"`
- Log-Artefakt:
  - `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-15_runDO_PB.log`

### 2) Nächste dokumentierte Kurzaufgabe (T5.x)
- Befehl:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec pytest -q tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only`
- Log-Artefakt:
  - `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-15_runDO.log`

## Ergebnis
- **N10-PB:** Prozesslauf erfolgreich mit Exit `0`; synthetischer AC0223-Repropfad ist als ausführbarer Fallback vorhanden.
- **T5.x:** Testlauf erfolgreich mit Exit `0` (`1 passed`), Laufzeit `92.53s`.

## Kurzfazit
Die geforderte Kombination aus „nächste dokumentierte Aufgabe + gekoppelte Plan-B-Aufgabe" wurde in derselben Session mit belastbaren Log-Artefakten umgesetzt.
