# Nächstes Arbeitspaket – IDO-11 Rechte rF-Connector-Heuristik Run QI (2026-06-18)

## Ziel

Run QI setzt den nach Run QH dokumentierten Anschluss aus
`docs/image_description_only_tasks.md` fort: Verbleibende rechte AC08-Familienregeln
sollen weiter auf messbare Relations-/Beschreibungssignale zurückgeführt werden.

## Umsetzung

- Die rF-Folgepunkte `AC0844` und `AC0864` werden nicht mehr über die
  Familien-ID-Liste als rechter Horizontalarm markiert.
- Beschreibungen wie „Griff nach unten“ laufen weiterhin über die bereits
  katalogfreie rechte Connector-Heuristik und erzeugen
  `SEMANTIC: waagrechter Strich rechts vom Kreis`.
- Der gezielte Semantiktest sichert zusätzlich, dass der rechte rF-Connector bei
  `AC0844` aus `description_heuristic` und nicht mehr aus `family_rule` stammt.
- Die Legacy-Ratchet-Baseline wurde aktualisiert und sinkt von 374 auf 372
  Runtime-ID-Vorkommen.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_semantic_family_rules_helpers.py
```

Ergebnis: Exit `0`; der Ratchet meldet `372 legacy occurrences remain`, und der
gezielte Beschreibung-/Semantik-Testblock läuft mit `37 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Beschreibung-/Semantik-Regressionen.
- **Ergebnis:** Exit `0`; `37 passed` im gezielten Testblock.
- **Blocker:** Kein neuer Blocker; die älteren rechten Basis-/CO₂-/VOC-Familienanker bleiben als nächster IDO-11-Abbau offen.
- **Dokumentation:** Rechte rF-Connectoren werden jetzt im Familienregelpfad über Beschreibungssignale statt über die explizite rechte Familienliste stabilisiert.
- **Nächster Schritt:** Die verbleibenden rechten Basis-/CO₂-/VOC-Connector-Anker auf dieselbe Relations-/Bildsignal-Strategie zurückführen.
