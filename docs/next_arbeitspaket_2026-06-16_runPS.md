# Nächstes Arbeitspaket – IDO-04 Holdout-/Rename-Protokoll Run PS (2026-06-16)

Dieses Arbeitspaket bearbeitet die nächste offene IDO-P0-Aufgabe aus
`docs/image_description_only_tasks.md`: **IDO-04 – Holdout- und
Rename-Evaluationsprotokoll definieren**.

## Umsetzung

- Neues Tool `tools/define_holdout_rename_protocol.py` erzeugt ein
  versioniertes JSON-Protokoll für `holdout_rename_protocol_v1`.
- Das Protokoll trennt Entwicklungs- und strikt zurückgehaltene Holdout-Samples,
  benennt Holdout-Dateien deterministisch mit einem katalogfreien SHA-256-Namen
  um und dokumentiert Leckageverbote.
- Der Metrikvertrag verlangt für beide Splits getrennte Pixel-, Kanten-,
  Struktur- und Semantikmetriken.
- Das Artefakt wurde unter
  `artifacts/evaluation/holdout_rename_protocol_v1/holdout_rename_protocol_v1.json`
  erzeugt.

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_holdout_rename_protocol.py`
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/define_holdout_rename_protocol.py`
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py`

## Ergebnis

IDO-04 ist abgeschlossen. Der nächste sinnvolle Schritt ist IDO-05:
Beschreibungsvokabular ohne Katalog-IDs als versioniertes Schema spezifizieren.
