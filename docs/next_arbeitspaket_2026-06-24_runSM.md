# Nächstes Arbeitspaket – IDO-16 Abschluss Globale Konfiguration Run SM (2026-06-24)

Run SM arbeitet nach Run SL die nächste noch offene dokumentierte Checkbox aus
`docs/image_description_only_tasks.md` ab: **IDO-16 – Globale Konfiguration v1
einführen**. Die funktionale Umsetzung lag bereits aus Run QR vor; dieses Paket
schließt den Dokumentationsstatus und sichert den Vertrag erneut ab.

## Prüfung

- `global_converter_config_v1` ist als katalogfreie, globale Konfiguration mit
  versionierter Default-Datei und JSON-Schema vorhanden.
- Die Validierung lehnt unbekannte Top-Level-Schlüssel und bildbezogene Bereiche
  wie `image_overrides`, `variant_name` oder `catalog_id` ab.
- Fehlende oder ungültige lokale Konfigurationsdateien fallen reproduzierbar auf
  die Defaults zurück.

## Änderungen

- `docs/image_description_only_tasks.md` markiert IDO-16 als abgeschlossen und
  ergänzt die Run-SM-Abschlussnotiz.
- `docs/README.md` verlinkt dieses Arbeitspaket in der Dokumentationsübersicht.

## Sicherung

- `python -m compileall -q src tests/detailtests/test_quality_config_helpers.py`
- `python tools/check_no_new_image_id_hardcoding.py`
- `pytest -q tests/detailtests/test_quality_config_helpers.py`

## Ergebnis

IDO-16 ist nun auch im Detailbacklog konsistent abgeschlossen: Die globale
Konfiguration erfüllt die dokumentierten Akzeptanzkriterien, bleibt frei von
Bild-/Katalogbereichen und die Runtime-ID-Nullprüfung bleibt grün.
