# Nächstes Arbeitspaket – IDO-11 Rechter Kreis-Connector Run QG (2026-06-17)

## Ziel

Run QG setzt den nach Run QF dokumentierten Anschluss aus
`docs/image_description_only_tasks.md` um: Rechte Kreis-Connectoren sollen über
denselben Richtungsparameter wie linke Connectoren generalisiert werden, statt
separate Finalisierungszweige pro AC08-Familie zu behalten.

## Umsetzung

- Der gemeinsame AC08-Horizontalarm-Finalisierungspfad akzeptiert jetzt
  `connector_direction=right` zusätzlich zu `left`.
- Rechte AC08-Connector-Varianten für einfache, CO₂-, VOC- und rF-Badges setzen
  die Richtung vor und nach optionalem Bild-Fitting und laufen anschließend durch
  die gemeinsame rechte Arm-Enforcement-Callback-Schnittstelle.
- Die zuvor wiederholten rechten `default -> optional fit -> finalize`-Branches
  sind damit an den parameterisierten Horizontalarm-Pfad angebunden.
- Die Legacy-Hardcoding-Baseline wurde nach dem Abbau aktualisiert: Der Ratchet
  sinkt von 379 auf 374 verbleibende Runtime-ID-Vorkommen.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_semantic_ac08_params_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py tests/detailtests/test_semantic_ac08_params_helpers.py
```

Ergebnis: Exit `0`; der Ratchet meldet `374 legacy occurrences remain`, und der
gezielte Beschreibung-/Semantik-/AC08-Parameter-Testblock läuft mit `39 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Beschreibung-/Semantik-/AC08-Parameter-Regressionen.
- **Ergebnis:** Exit `0`; `39 passed` im gezielten Testblock.
- **Blocker:** Kein neuer Blocker; vollständige IDO-11-Relations-/Rename-Abnahme bleibt offen.
- **Dokumentation:** Dieser Run generalisiert rechte AC08-Horizontalconnector-Finalisierung über denselben Richtungsparameter wie links.
- **Nächster Schritt:** Rechte Connector-Relationen in Beschreibung/Constraints explizit spiegeln und mit neutralen Rename-Tests absichern.
