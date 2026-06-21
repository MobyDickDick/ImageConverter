# Nächstes Arbeitspaket – IDO-17 Text-/Hilfetext-Neutralisierung Run RS (2026-06-21)

Run RS setzt IDO-17 aus `docs/image_description_only_tasks.md` fort: weitere
nicht entscheidungsrelevante Katalog-ID-Nennungen in Kommentaren, Docstrings und
CLI-Ausgaben werden durch neutrale Topologie- und Paketbegriffe ersetzt, ohne
funktionale Dispatches oder historische Kompatibilitätsnamen umzubauen.

## Dokumentierte Aufgabe

- **Aufgabe:** IDO-17 – Runtime-Code von Katalog-IDs befreien.
- **Ziel dieses kleinen Pakets:** verbleibende rein erklärende Referenzen in
  Hilfetexten, Logs und Dokumentationsstrings neutralisieren und anschließend die
  Legacy-Ratchet-Baseline aktualisieren.

## Umsetzung

- Die interaktive Bereichsauswahl beschreibt gekürzte/paarige Präfixfilter nun
  ohne konkrete Beispiel-ID.
- Automatische Isolated-Render-Hinweise und die Regressionsauswahl sprechen von
  Semantic-Badge-Regression beziehungsweise Semantic-Badge-Vollbereich statt von
  konkreten Katalogbereichen.
- Donor-Template- und Quality-Pass-Docstrings verwenden neutrale
  Semantic-Badge-Begriffe statt Katalogfamilienbeispiele.
- Converter-Kommentare für adaptive Locks, kompakte Badge-Defaults und
  Badge-Grauwerte sowie der CO₂-Default-Helper-Docstring sind katalogfrei
  formuliert.
- Die Legacy-Ratchet-Baseline wurde nach dem Abbau aktualisiert.

## Ergebnis

- `tools/check_no_new_image_id_hardcoding.py` bleibt grün.
- Die Legacy-Inventur sinkt von `177` auf `173` Runtime-ID-Vorkommen.
- Kein neuer funktionaler Blocker; die verbleibenden IDO-17-Vorkommen enthalten
  weiterhin echte Runtime-Dispatches, historische API-Namen und noch nicht
  migrierte Metadatenpfade, die separat semantisch ersetzt werden müssen.
