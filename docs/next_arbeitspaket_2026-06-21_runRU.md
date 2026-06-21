# Nächstes Arbeitspaket – IDO-17 AR-Badge-Helper-Neutralisierung Run RU (2026-06-21)

Run RU setzt IDO-17 aus `docs/image_description_only_tasks.md` fort: weitere
nicht entscheidungsrelevante Katalog-ID-Nennungen in Runtime-Docstrings werden
durch neutrale Topologie- und Helper-Begriffe ersetzt, ohne funktionale
Dispatches, Kompatibilitätsnamen oder Geometrieparameter umzubauen.

## Dokumentierte Aufgabe

- **Aufgabe:** IDO-17 – Runtime-Code von Katalog-IDs befreien.
- **Ziel dieses kleinen Pakets:** die verbliebenen rein erklärenden Badge-Helper-
  Docstrings im AR-Badge-Modul neutralisieren und anschließend die Legacy-
  Ratchet-Baseline aktualisieren.

## Umsetzung

- Der Modul-Docstring des skalierten Badge-Parameter-Helpers verwendet nun eine
  katalogfreie Beschreibung statt eines konkreten historischen Symbols.
- Der Funktions-Docstring des Default-Badge-Parameter-Builders beschreibt die
  scale-adapted Geometry und zentrierte Glyph-Bounding-Box ohne Katalog-ID.
- Die Legacy-Ratchet-Baseline wurde nach dem Abbau aktualisiert.

## Ergebnis

- `tools/check_no_new_image_id_hardcoding.py` bleibt grün.
- Die Legacy-Inventur sinkt von `160` auf `158` Runtime-ID-Vorkommen.
- Kein neuer funktionaler Blocker; die verbleibenden IDO-17-Vorkommen enthalten
  weiterhin echte Runtime-Dispatches, historische API-Namen und noch nicht
  migrierte Metadatenpfade, die separat semantisch ersetzt werden müssen.
