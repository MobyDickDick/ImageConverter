# Nächstes Arbeitspaket – T6.11 automatisierte Blocker-Inventur Run PU (2026-06-15)

## Ziel

Run PU automatisiert die in `docs/open_tasks.md` geforderte wiederholbare
Blocker-Inventur. Jeder Lauf soll den vollständigen pytest-Befehl ausführen,
ein dauerhaftes Run-Log schreiben und die aktuelle Top-20-Laufzeitliste im
Aufgabendokument reproduzierbar ersetzen.

## Umsetzung

- Neues Werkzeug `tools/run_blocker_inventory.py`:
  - verwendet standardmäßig
    `python -m pytest --maxfail=1 -vv --durations=20`;
  - schreibt die kombinierte pytest-Ausgabe unter
    `artifacts/converted_images/reports/blocker_inventory_<run-id>.log`;
  - extrahiert Durationszeilen und fehlgeschlagene Test-Nodes;
  - sortiert die Laufzeiten absteigend;
  - ersetzt ausschließlich den durch HTML-Marker begrenzten Inventurabschnitt
    in `docs/open_tasks.md`;
  - gibt den pytest-Exit-Code unverändert zurück.
- Neue fokussierte Tests prüfen Sortierung, Begrenzung, Failure-Erkennung und
  idempotentes Ersetzen des Dokumentabschnitts.
- T6.11 wurde nach dem erfolgreichen realen Inventurlauf abgeschlossen.

## Laufnachweis

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. \
python tools/run_blocker_inventory.py --run-id 2026-06-15-runPU
```

| Kriterium | Run PU |
| --- | --- |
| pytest-Exit | `0` |
| Ergebnis | `818 passed` |
| Laufzeit | `68.22s` |
| Log | `artifacts/converted_images/reports/blocker_inventory_2026-06-15-runPU.log` |
| Dokumentaktualisierung | Top-20-Tabelle in `docs/open_tasks.md` |

Die aktuelle Inventur enthält keine fehlgeschlagenen Nodes. Der längste Test
ist
`test_release_candidate_gate_propagates_paths_to_segmented_smoke`
mit `10.61s`; die fünf längsten Einträge stammen sämtlich aus den
Release-Candidate-/Segmented-Smoke-Helfertests.

## 5-Zeilen-Log

- **Getestet:** Vollständige pytest-Inventur mit `--maxfail=1 -vv --durations=20`.
- **Ergebnis:** Exit `0`, `818 passed in 68.22s`; Run-Log und Top-20-Tabelle wurden erzeugt.
- **Blocker:** Keine fehlgeschlagenen Test-Nodes; aktuelle Laufzeitspitze `10.61s`.
- **Nächster Schritt:** T6.12, den AC0800-L-Regressionsfall isolieren und unter das 120-Sekunden-Ziel bringen.
- **Startbefehl:** `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q 'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0800_L-semantic_ok]'`.
