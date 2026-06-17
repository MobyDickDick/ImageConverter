# Nächstes Arbeitspaket – IDO-10 Linker Kreis-Connector Run QC (2026-06-17)

## Ziel

Run QC arbeitet am nächsten offenen Paket aus `docs/image_description_only_tasks.md`:
**IDO-10 – Linker Kreis-Connector als erstes vertikales Migrationspaket**. Der
linke Kreis-Connector soll aus Beschreibungstext und messbaren Relationen statt
aus Katalog-/Bild-ID-Listen ableitbar sein.

## Umsetzung

- Der Beschreibung-Constraint-Vertrag übernimmt die explizite
  `left_of`-Relation des linken Kreis-Connectors nun maschinenlesbar in
  `description_constraints.relations`.
- Die semantische Beschreibungsauswertung erkennt zusätzlich relationale Texte
  wie „Linie links vom Kreis“, „Strich links vom Kreis“ und „Anschluss links vom
  Kreis“ als linken horizontalen Kreis-Connector.
- Neue neutrale Regressionen sichern den katalogfreien Pfad ohne AC08-Familien-ID:
  `CircleBackground` + `HorizontalRule`, `target_ref=described_circle` und
  `left_of`-Relation.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tools tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py
```

Ergebnis: Exit `0`; der Ratchet meldet keine neuen Runtime-Bild-IDs über der
Legacy-Baseline, und der gezielte Beschreibung-/Semantik-Testblock läuft mit
`31 passed`.

## 5-Zeilen-Log

- **Getestet:** Katalogfreie Relation `Linie links vom Kreis` im Constraint- und Semantikpfad.
- **Ergebnis:** Exit `0`; `31 passed` im gezielten Testblock.
- **Blocker:** Kein neuer Blocker; vollständiger Baseline-Abbau für IDO-10 bleibt offen.
- **Dokumentation:** Dieser Run dokumentiert den ersten vertikalen IDO-10-Schritt ohne neue Bild-ID-Abhängigkeit.
- **Nächster Schritt:** Linke Kreis-Connector-Familien aus verbleibenden AC08-Listen auf die generische Relation umstellen und Baseline-Einträge reduzieren.
