# Nächstes Arbeitspaket – IDO-18 Legacy-Ratchet-Entfernung Run SH (2026-06-23)

Run SH arbeitet nach Abschluss von IDO-17 das nächste dokumentierte Arbeitspaket aus `docs/image_description_only_tasks.md` ab: **IDO-18 – Legacy-Baseline und Ratchet entfernen**.

## Änderungen

- `config/legacy_image_id_baseline.json` wurde gelöscht; es gibt keine Runtime-ID-Allowlist mehr.
- `tools/check_no_new_image_id_hardcoding.py` scannt `src/` jetzt als absolute Nullprüfung. Jede gefundene Katalog-/Bild-ID (`AC`, `AR`, `GE`, `DLG`, `SE`) erzeugt einen Fehler ohne Baseline-Vergleich.
- Der CLI-Test nutzt keine temporäre Baseline mehr und sichert, dass eine synthetische Runtime-ID direkt abgelehnt wird.
- Workflow- und Architektur-Dokumentation benennen die Prüfung als Null-Gate statt als Migrations-Ratchet.

## Sicherung

- `python tools/check_no_new_image_id_hardcoding.py` meldet `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_no_new_image_id_hardcoding.py` läuft grün.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m compileall -q tools tests` läuft grün.

## Ergebnis

IDO-18 ist abgeschlossen: Die temporäre Legacy-Baseline ist entfernt, der Check benötigt keine Allowlist mehr und verbietet jede Bild-ID in Runtime-Quellen absolut.
