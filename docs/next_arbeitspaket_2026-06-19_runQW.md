# Nächstes Arbeitspaket – IDO-17 Semantic-Quality-Marker Run QW (2026-06-19)

## Ziel

Run QW setzt IDO-17 aus `docs/image_description_only_tasks.md` als kleines
Folgepaket nach Run QV fort: Ein weiterer Runtime-Katalog-ID-Guard wird aus der
semantischen Qualitätsannotation entfernt. Borderline-Hinweise für erfolgreiche
Semantic-Badge-Konvertierungen sollen nicht mehr an `AC0811`, sondern an die
gemessenen Elementfehler gekoppelt sein.

## Umsetzung

- `semanticQualityFlagsImpl(...)` wertet jetzt die vorhandenen
  Element-Validation-Logs katalogfrei aus.
- Der bisherige `AC0811`-Namensguard wurde entfernt; die numerischen
  Schwellen (`highest_error >= 10.0` oder mindestens zwei Elemente ab `8.0`)
  bleiben unverändert.
- Ein neutraler Regressionstest mit `ZZ_NEUTRAL_BADGE` sichert, dass
  Borderline-Hinweise ohne Katalog-ID erzeugt werden.
- Die Legacy-Ratchet-Baseline wurde nach der Entfernung des Namensguards von
  330 auf 329 Runtime-ID-Vorkommen abgesenkt.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_semantic_quality_flags.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_semantic_quality_flags.py
```

Ergebnis: Exit `0`; der Ratchet meldet `329 legacy occurrences remain`, und der
gezielte Semantic-Quality-Testblock läuft mit `5 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Semantic-Quality-Regressionen.
- **Ergebnis:** Exit `0`; `5 passed`, Ratchet jetzt `329`.
- **Blocker:** IDO-17 ist noch nicht abgeschlossen; weitere Runtime-Katalog-IDs bleiben in anderen Spezialpfaden.
- **Dokumentation:** IDO-17 dokumentiert den weiteren Baseline-Abbau und die elementfehlerbasierte Quality-Markierung.
- **Nächster Schritt:** IDO-17 fortsetzen und weitere ID-spezifische Runtime-Guards in struktur-/beschreibungsgesteuerte Parameter überführen.
