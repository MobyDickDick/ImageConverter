# Nächstes Arbeitspaket – Run RN (2026-06-21)

Run RN setzt den in `docs/image_description_only_tasks.md` dokumentierten IDO-17-Anschluss fort: verbleibende Katalog-ID-Vorkommen in `src/` werden weiter aus der Runtime herausgelöst beziehungsweise auf neutrale Dokumentation umgestellt.

## Dokumentierte Aufgabe

- **Aufgabe:** IDO-17 – Runtime-Code von Katalog-IDs befreien.
- **Ziel dieses kleinen Pakets:** weitere offensichtliche, nicht entscheidungsrelevante Katalog-ID-Nennungen in Kommentaren und Docstrings neutralisieren, ohne semantische Pfade, Parameterdispatch oder Spezialfälle funktional umzubauen.

## Umsetzung

- Docstrings der Semantic-Badge-Helfer beschreiben die betroffenen Topologien nun über neutrale Begriffe wie lower-vertical, left-horizontal, top-connector und right-horizontal statt über konkrete Kataloganker.
- Familienweite Guardrail-Docstrings und Kommentare sprechen von Circle-Badge- beziehungsweise Connector-Badge-Familien statt von konkreten Katalogbereichen.
- Ein Non-Composite-Kommentar beschreibt den betroffenen Pfad über die diagonale/Gradienten-Topologie statt über eine Beispiel-ID.
- Die Legacy-Ratchet-Baseline wurde nach dem Abbau aktualisiert.

## Ergebnis

- `tools/check_no_new_image_id_hardcoding.py` bleibt grün.
- Die Legacy-Inventur sinkt von `246` auf `220` Runtime-ID-Vorkommen.
- Kein neuer funktionaler Blocker; die verbleibenden IDO-17-Vorkommen liegen weiterhin überwiegend in aktiven Dispatch-, Metadaten- und Kompatibilitätspfaden und müssen in nachgelagerten Paketen semantisch ersetzt werden.
