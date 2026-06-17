# Nächstes Arbeitspaket – IDO-10 Linker Kreis-Connector Run QF (2026-06-17)

## Ziel

Run QF setzt den nach Run QE dokumentierten IDO-10-Anschluss um: Verbleibende
Linksconnector-Dispatches sollen stärker aus Parameter-/Relationssignalen statt
aus wiederholten Familienzweigen abgeleitet werden.

## Umsetzung

- Die linken AC08-Horizontal-Connector-Varianten laufen jetzt durch einen
  gemeinsamen `_finalize_left_arm_badge_params(...)`-Pfad.
- Der gemeinsame Pfad setzt `connector_direction=left` vor und nach optionalem
  Bild-Fitting und ruft danach dieselbe linke Arm-Enforcement-Logik auf.
- Die vorher mehrfach duplizierten `finalize -> enforce_left_arm`-Branches für
  einfache, CO₂-, VOC- und rF-Linksconnector-Badges wurden dadurch gebündelt.
- Die Legacy-Hardcoding-Baseline wurde nach dem Abbau aktualisiert: Der Ratchet
  sinkt von 382 auf 379 verbleibende Runtime-ID-Vorkommen.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tools tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py
```

Ergebnis: Exit `0`; der Ratchet meldet `379 legacy occurrences remain`, und der
gezielte Beschreibung-/Semantik-Testblock läuft mit `33 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Beschreibung-/Semantik-Regressionen.
- **Ergebnis:** Exit `0`; `33 passed` im gezielten Testblock.
- **Blocker:** Kein neuer Blocker; vollständiger IDO-10-Baseline-Abbau bleibt offen.
- **Dokumentation:** Dieser Run zentralisiert den linken Connector-Finalisierungspfad und aktualisiert den Ratchet.
- **Nächster Schritt:** Rechte Kreis-Connectoren in IDO-11 über denselben Richtungsparameter generalisieren.
