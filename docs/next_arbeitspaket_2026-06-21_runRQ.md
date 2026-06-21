# Nächstes Arbeitspaket – IDO-17 Kommentar-/CLI-Neutralisierung Run RQ (2026-06-21)

Run RQ setzt IDO-17 aus `docs/image_description_only_tasks.md` fort und arbeitet zusätzlich eine gekoppelte Plan-B-Pflegeaufgabe ab.

## Dokumentierte Aufgabe

- **Aufgabe:** IDO-17 – Runtime-Code von Katalog-IDs befreien.
- **Ziel dieses kleinen Pakets:** weitere nicht entscheidungsrelevante Katalog-ID-Nennungen in CLI-Hilfetexten, Kommentaren und Docstrings neutralisieren, ohne funktionale Dispatches umzubauen.

## Umsetzung

- CLI-Beispiele, Debug-Hilfetexte und Valve-Head-Reparaturmeldungen verwenden neutrale Bereichs-/Topologiebegriffe statt konkrete Kataloganker.
- Dual-Stem-/Triangle-Detection-Docstrings und Fallback-Kommentare beschreiben die Formklasse ohne konkrete Bild-ID.
- Template-Transfer-Kommentare für Valve-Head-, Dual-Arrow- und Description-driven-IR-Schutzpfade wurden katalogfrei formuliert.
- Die Legacy-Ratchet-Baseline wurde nach dem Abbau aktualisiert.

## Gekoppelte Plan-B-Aufgabe

- Der Conversion-Quality-Review wurde reproduzierbar mit `tools/review_conversion_quality.py --max-candidates 5` erneuert.
- Die aktive Plan-B-Liste wurde auf die aktuell qualifizierten Diff-Kandidaten `GE1001_M` und `GE9021_7M` umgestellt.
- Der PF8-Linkage-Report wurde erneut ausgeführt und auf die GE1001/GE9021-Rotation ausgerichtet; `GE1001_M` ist als generalisierter Kreis-/Linien-Seed dokumentiert, `GE9021_7M` als Linienhinweis `nur Sonderfall`.

## Ergebnis

- `tools/check_no_new_image_id_hardcoding.py` bleibt grün.
- Die Legacy-Inventur sinkt von `195` auf `182` Runtime-ID-Vorkommen.
- Kein neuer funktionaler Blocker; die verbleibenden IDO-17-Vorkommen enthalten weiterhin echte Runtime-Dispatches und historisch benannte APIs, die separat migriert werden müssen.
