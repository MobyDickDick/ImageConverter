# Nächstes Arbeitspaket – IDO-10 Linker Kreis-Connector Run QE (2026-06-17)

## Ziel

Run QE arbeitet den nächsten offenen IDO-10-Schritt aus
`docs/image_description_only_tasks.md` ab: Nach den Synonym-/Invers-Relationen
wird die Legacy-Baseline weiter reduziert, indem linke/rechte Connector-Guards
und Transfer-Kommentare nicht mehr über konkrete Katalogfamilien beschrieben
werden.

## Umsetzung

- Die linken und rechten Horizontal-Connector-Guards beschreiben ihre Aufgabe
  jetzt neutral über Connector-Richtung und sichtbaren horizontalen Arm statt
  über Beispiel-Bild-IDs.
- Transfer- und Validierungslogik dokumentieren gerichtete Connectoren jetzt als
  parametergesteuerte Geometrie, nicht mehr als konkrete Familienbeispiele.
- Die Legacy-Hardcoding-Baseline wurde nach dem Abbau aktualisiert: Der Ratchet
  sinkt von 395 auf 382 verbleibende Runtime-ID-Vorkommen.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tools tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py
```

Ergebnis: Exit `0`; der Ratchet meldet `382 legacy occurrences remain`, und der
gezielte Beschreibung-/Semantik-Testblock läuft mit `33 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Beschreibung-/Semantik-Regressionen.
- **Ergebnis:** Exit `0`; `33 passed` im gezielten Testblock.
- **Blocker:** Kein neuer Blocker; vollständiger IDO-10-Baseline-Abbau bleibt offen.
- **Dokumentation:** Dieser Run reduziert IDO-10-bezogene Katalog-ID-Beispiele in Runtime-Kommentaren/Logs.
- **Nächster Schritt:** Verbleibende Linksconnector-Dispatches aus Parameter-/Relationssignalen statt Familiennamen ableiten.
