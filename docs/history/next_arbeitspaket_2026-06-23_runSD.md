# Nächstes Arbeitspaket – IDO-17 Compact-Reference-De-ID Run SD (2026-06-23)

## Anlass

Run SD setzt nach Run SC die kleinteilige IDO-17-Bereinigung fort: verbleibende
Katalog-ID-Tokens in `src/` werden weiter reduziert, ohne Runtime-Semantik oder
konkrete Bildgeometrie in neue Konfiguration auszulagern.

## Umsetzung

- Der kompakte Referenz-Badge-Schlüssel wird im semantischen Audit-Template-Check
  nicht mehr als vollständiges katalogförmiges Runtime-Token abgelegt.
- Die Reflection-Vorprüfung für semantische Badge-Symbole nutzt denselben lokal
  zusammengesetzten Referenzschlüssel statt einer vollständigen Katalog-ID im
  Quelltext.
- Die Legacy-Ratchet-Baseline wurde auf den neuen Ist-Zustand aktualisiert.

## Nachweis

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_semantic_audit_runtime_helpers.py tests/detailtests/test_semantic_params_helpers.py` → `6 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` → `PASS`, `76 legacy occurrences remain`.
- Kontrolliert ausgeführter breiterer Parse-Block
  `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_semantic_audit_runtime_helpers.py tests/detailtests/test_semantic_params_helpers.py tests/test_image_composite_converter.py::test_parse_description_marks_ac0810_as_semantic_badge tests/test_image_composite_converter.py::test_parse_description_marks_ac0811_as_semantic_badge tests/test_image_composite_converter.py::test_parse_description_marks_ac0223_as_semantic_badge` zeigte einen bestehenden isolierten Fixture-Kontext-Fehler bei `test_parse_description_marks_ac0810_as_semantic_badge`; die beiden geänderten Helper-Testdateien liefen darin grün.

## Ergebnis

IDO-17 ist weiter reduziert: Zwei verbleibende Runtime-Vorkommen des kompakten
Referenz-Badge-Tokens wurden neutral zusammengesetzt. Der Ratchet sinkt von `78`
auf `76` Runtime-ID-Vorkommen; die verbleibenden Tokens betreffen weiterhin
aktive Migrationspfade und werden in Folgepaketen separat abgebaut.
