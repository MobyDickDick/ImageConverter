# Nächstes Arbeitspaket – IDO-10 Linker Kreis-Connector Run QC (2026-06-17)

## Ziel

Run QC bearbeitet den ersten Teil von `docs/image_description_only_tasks.md`:
**IDO-10 – Linker Kreis-Connector als erstes vertikales Migrationspaket**.
Die semantische Kennzeichnung „waagrechter Strich links vom Kreis“ soll nicht
mehr aus einer katalogspezifischen Familienliste entstehen, sondern aus der
textuellen Beschreibung des Symbols.

## Umsetzung

- Die Erkennung des linken Kreis-Connectors wurde in einen generischen
  Beschreibungstest ausgelagert: Kreis-/Badge-Kontext plus horizontale
  Connector-Hinweise und explizite Linksrelation ergeben das semantische Element.
- Die bisherige AC08-Familienliste für den linken Connector wurde aus der
  semantischen Familienregel entfernt; der Connector landet nun in
  `description_heuristic` statt in `family_rule`.
- Die finale Connector-Durchsetzung aktiviert die linke Armgeometrie nur noch,
  wenn das semantische Element tatsächlich vorliegt, nicht wegen bestimmter
  Bild-IDs.
- Die Legacy-Ratchet-Baseline wurde nach dem Abbau der Runtime-ID-Vorkommen
  aktualisiert.

## Laufzeit- und Akzeptanznachweis

```bash
python -m pytest -q tests/detailtests/test_semantic_family_rules_helpers.py tests/detailtests/test_semantic_connector_helpers.py
python tools/check_no_new_image_id_hardcoding.py
```

Ergebnis: Beide Checks laufen mit Exit `0`; der gezielte Helper-Testblock läuft
mit `9 passed`, und der Ratchet meldet `395 legacy occurrences remain`.

## 5-Zeilen-Log

- **Getestet:** Generische Links-Connector-Erkennung aus Beschreibung plus Connector-Enforcement ohne Links-ID-Liste.
- **Ergebnis:** Exit `0`; `9 passed` im gezielten Helper-Testblock.
- **Blocker:** IDO-10 ist noch nicht vollständig abgeschlossen; weitere linke-Connector-Dispatches in Parameter-/Fitting-Pfaden bleiben zu migrieren.
- **Dokumentation:** Dieser Run dokumentiert den ersten Ratchet-Abbau innerhalb IDO-10.
- **Nächster Schritt:** Die verbleibenden AC0812-/AC0832-/AC0837-/AC0842-/AC0862-/AC0882-Parameterpfade auf messbare Connector-Eigenschaften und Beschreibungssignale umstellen.
