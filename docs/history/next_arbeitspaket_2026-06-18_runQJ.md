# Nächstes Arbeitspaket – IDO-11 Rechte Basis-/CO₂-/VOC-Connector-Anker Run QJ (2026-06-18)

## Ziel

Run QJ setzt den nach Run QI dokumentierten Anschluss aus
`docs/image_description_only_tasks.md` fort: Die verbleibenden rechten
Basis-/CO₂-/VOC-Connector-Anker sollen aus der expliziten Familien-ID-Regel
entfernt und über messbare Beschreibungs-/Relationssignale stabilisiert werden.

## Umsetzung

- Die rechten Horizontalarm-Familienanker `AC0810`, `AC0814`, `AC0834` und
  `AC0839` werden nicht mehr über die `family_rule`-ID-Liste als rechter
  Connector markiert.
- Die Beschreibungserkennung für rechte Kreis-Connectoren deckt nun zusätzlich
  knappe Formulierungen wie „Griff unten“/„Anschluss unten“ sowie die
  dokumentierte „gegenüberliegende Drehlage“ ab.
- Ein gezielter Semantiktest prüft für Basis-, CO₂-/Text- und VOC-artige rechte
  Folgevarianten, dass `SEMANTIC: waagrechter Strich rechts vom Kreis` aus
  `description_heuristic` und nicht aus `family_rule` stammt.
- Die Legacy-Ratchet-Baseline wurde aktualisiert und sinkt von 372 auf 368
  Runtime-ID-Vorkommen.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py
```

Ergebnis: Exit `0`; der Ratchet meldet `368 legacy occurrences remain`, und der
gezielte Beschreibung-/Semantik-Testblock läuft mit `38 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Beschreibung-/Semantik-Regressionen.
- **Ergebnis:** Exit `0`; `38 passed` im gezielten Testblock.
- **Blocker:** Kein neuer Blocker; IDO-11 ist im Semantik-Familienregelpfad für rechte Horizontalarme abgebaut, weitere Runtime-ID-Dispatches bleiben separat offen.
- **Dokumentation:** Rechte Basis-/CO₂-/VOC-Connectoren werden jetzt wie die rF-Folgepunkte aus Beschreibungssignalen statt über eine explizite rechte Familienliste stabilisiert.
- **Nächster Schritt:** IDO-12 starten und obere/untere Kreis-Connectoren anhand von Beschreibung, Z-Order und Bildgeometrie generalisieren.
