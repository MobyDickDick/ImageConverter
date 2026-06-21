# Nächstes Arbeitspaket – Run RM (2026-06-21)

Run RM setzt den in `docs/image_description_only_tasks.md` dokumentierten IDO-17-Anschluss fort: verbleibende Katalog-ID-Vorkommen in `src/` werden weiter aus der Runtime herausgelöst beziehungsweise auf neutrale Dokumentation umgestellt.

## Dokumentierte Aufgabe

- **Aufgabe:** IDO-17 – Runtime-Code von Katalog-IDs befreien.
- **Ziel dieses kleinen Pakets:** offensichtliche, nicht entscheidungsrelevante Katalog-ID-Nennungen in Kommentaren, Docstrings und Runtime-Logtexten neutralisieren, ohne die bestehenden semantischen Pfade oder Spezialfälle umzubauen.

## Umsetzung

- Symmetric-Chord-, right-rotated-valve- und Geometry-IR-Kommentare beschreiben die betroffenen Topologien nun über neutrale Form-/Topologiebegriffe statt über konkrete Kataloganker.
- Optimizer-Docstrings für den right-rotated-valve-Fit verwenden keine konkrete Bild-ID mehr.
- Ein deutschsprachiger Geometry-IR-Logtext für referenzartige Kreuz-/Kühlelement-Beschreibungen wurde neutral formuliert.
- Die Legacy-Ratchet-Baseline wurde nach dem Abbau aktualisiert.

## Ergebnis

- `tools/check_no_new_image_id_hardcoding.py` bleibt grün.
- Die Legacy-Inventur sinkt von `254` auf `246` Runtime-ID-Vorkommen.
- Kein neuer funktionaler Blocker; die verbleibenden IDO-17-Vorkommen sind weiterhin in nachgelagerten Runtime-/Metadatenpaketen abzubauen.
