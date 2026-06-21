# Nächstes Arbeitspaket – IDO-17 CLI-Optionsnamen-Neutralisierung Run RV (2026-06-21)

Run RV setzt IDO-17 aus `docs/image_description_only_tasks.md` fort: zwei
verbliebene katalogspezifische, rein bedienoberflächennahe CLI-Optionsnamen
werden durch neutrale Bezeichnungen ersetzt, ohne die bestehenden internen
Callback-/Namespace-Namen umzubauen.

## Dokumentierte Aufgabe

- **Aufgabe:** IDO-17 – Runtime-Code von Katalog-IDs befreien.
- **Ziel dieses kleinen Pakets:** katalogspezifische CLI-Schalter für fokussierte
  Semantic-Diff-Dumps und Valve-Head-Bestlist-Reparaturen neutralisieren und die
  Legacy-Ratchet-Baseline aktualisieren.

## Umsetzung

- Der fokussierte Debug-Ausgabeordner wird nun über den neutralen
  `--debug-semantic-focus-dir`-Schalter befüllt; das bestehende argparse-`dest`
  bleibt für nachgelagerte Runtime-Kompatibilität unverändert.
- Die einmalige Valve-Head-Bestlist-Reparatur wird nun über
  `--repair-valve-head-bestlist` aktiviert; auch hier bleibt das bestehende
  argparse-`dest` für die internen Aufrufer unverändert.
- Die Legacy-Ratchet-Baseline wurde nach dem Abbau aktualisiert.

## Ergebnis

- `tools/check_no_new_image_id_hardcoding.py` bleibt grün.
- Die Legacy-Inventur sinkt von `158` auf `156` Runtime-ID-Vorkommen.
- Kein neuer funktionaler Blocker; die verbleibenden IDO-17-Vorkommen enthalten
  weiterhin echte Runtime-Dispatches, historische API-Namen und noch nicht
  migrierte Metadatenpfade, die separat semantisch ersetzt werden müssen.
