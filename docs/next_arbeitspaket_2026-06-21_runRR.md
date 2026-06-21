# Nächstes Arbeitspaket – IDO-17 Kommentar-Neutralisierung Run RR (2026-06-21)

Run RR setzt IDO-17 aus `docs/image_description_only_tasks.md` fort: verbleibende Katalog-ID-Vorkommen in `src/` werden weiter aus der Runtime herausgelöst beziehungsweise auf neutrale Dokumentation umgestellt.

## Dokumentierte Aufgabe

- **Aufgabe:** IDO-17 – Runtime-Code von Katalog-IDs befreien.
- **Ziel dieses kleinen Pakets:** weitere nicht entscheidungsrelevante Katalog-ID-Nennungen in Kommentaren und Docstrings neutralisieren, ohne funktionale Dispatches, Spezialfälle oder Parameterpfade umzubauen.

## Umsetzung

- Der CO₂-Default-Kommentar im Semantic-Badge-Pfad beschreibt die betroffene Topologie nun als plain centered CO₂ badge statt über einen konkreten Kataloganker.
- Der Top-Stem-Connector-Docstring und der VOC-Kreisplatzierungs-Kommentar verwenden neutrale Topologiebegriffe statt Beispiel-IDs.
- Bestlist-Kommentare und Docstrings für Three-Way-Valve-Artefakte beschreiben die semantische Bedingung nun katalogfrei.
- Die Legacy-Ratchet-Baseline wurde nach dem Abbau aktualisiert.

## Ergebnis

- `tools/check_no_new_image_id_hardcoding.py` bleibt grün.
- Die Legacy-Inventur sinkt von `182` auf `177` Runtime-ID-Vorkommen.
- Kein neuer funktionaler Blocker; die verbleibenden IDO-17-Vorkommen enthalten weiterhin echte Runtime-Dispatches, historisch benannte APIs und Metadatenpfade, die separat semantisch ersetzt werden müssen.
