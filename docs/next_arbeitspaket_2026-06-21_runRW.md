# Nächstes Arbeitspaket – IDO-17 Centered-Triangle-Marker Run RW (2026-06-21)

Run RW setzt IDO-17 aus `docs/image_description_only_tasks.md` fort: verbleibende Katalog-ID-Vorkommen in `src/` werden weiter aus der Runtime herausgelöst beziehungsweise auf neutrale Dokumentation umgestellt.

## Dokumentierte Aufgabe

- **Aufgabe:** IDO-17 – Runtime-Code von Katalog-IDs befreien.
- **Ziel dieses kleinen Pakets:** katalogspezifische Marker in Debug-Logs und SVG-Struktur des Centered-Triangle-Helfers neutralisieren, ohne die Geometrie- oder Optimierungslogik umzubauen.

## Umsetzung

- Fallback-, Mess- und Iterationslogs des Centered-Triangle-Helfers verwenden nun den neutralen Präfix `centered-triangle` statt einer konkreten Katalog-ID.
- Die generierte SVG-Gruppe heißt nun `centered_triangle` und beschreibt damit die Topologie statt den historischen Bildanker.
- Die Detailtests wurden auf die neutralen Logmarker angepasst.
- Die Legacy-Ratchet-Baseline wurde nach dem Abbau aktualisiert.

## Ergebnis

- `tools/check_no_new_image_id_hardcoding.py` bleibt grün.
- Die Legacy-Inventur sinkt von `156` auf `148` Runtime-ID-Vorkommen.
- Kein neuer funktionaler Blocker; die verbleibenden IDO-17-Vorkommen enthalten weiterhin echte Runtime-Dispatches, historisch benannte APIs und Metadatenpfade, die separat semantisch ersetzt werden müssen.
