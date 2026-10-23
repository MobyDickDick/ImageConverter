# Nächstes Arbeitspaket – IDO-11 Rechte Connector-Relationen Run QH (2026-06-17)

## Ziel

Run QH setzt den nach Run QG dokumentierten Anschluss aus
`docs/image_description_only_tasks.md` um: Rechte Kreis-Connectoren sollen nicht
nur im AC08-Finalisierungspfad, sondern auch in Beschreibung, Constraints und
neutralen Rename-Tests katalogfrei gespiegelt werden.

## Umsetzung

- Der Beschreibung-zu-Geometry-IR-Pfad erkennt jetzt rechte Kreis-Connectoren
  über messbare Relationsformulierungen wie „rechts vom Kreis“, „rechter
  Anschluss“ und die inverse Form „Kreis links von der Linie“.
- Der erzeugte Constraint-Vertrag enthält für rechte Horizontalarme dieselbe
  Primitive-Kette wie links (`CircleBackground` + `HorizontalRule`), aber mit
  expliziter `right_of`-Relation und `target_ref=described_circle`.
- Die semantischen Beschreibung-Heuristiken wurden um denselben rechten
  Relationswortschatz erweitert, sodass rechte Connectoren ohne AC08-Familien-ID
  als `SEMANTIC: waagrechter Strich rechts vom Kreis` in den Badge-Pfad laufen.
- Neue neutrale Rename-Regressionen prüfen, dass rechte Connector-Beschreibungen
  unter katalogfremden Dateinamen identische Constraints und Geometry-IR liefern.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py
```

Ergebnis: Exit `0`; der Ratchet bleibt bei `374 legacy occurrences remain`, und
der gezielte Beschreibung-/Semantik-Testblock läuft mit `37 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Beschreibung-/Semantik-Regressionen.
- **Ergebnis:** Exit `0`; `37 passed` im gezielten Testblock.
- **Blocker:** Kein neuer Blocker; vollständiger Abbau der übrigen IDO-11-ID-Dispatches bleibt offen.
- **Dokumentation:** Rechte Kreis-Connectoren sind im Beschreibungspfad jetzt symmetrisch zu linken Connectoren über `right_of` modelliert.
- **Nächster Schritt:** Verbleibende rechte AC08-Familienregeln auf messbare Relations-/Bildsignale zurückführen und Baseline weiter senken.
