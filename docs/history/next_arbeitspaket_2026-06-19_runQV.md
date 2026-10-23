# Nächstes Arbeitspaket – IDO-17 Plain-Left-Arm-Validation Run QV (2026-06-19)

## Ziel

Run QV setzt IDO-17 aus `docs/image_description_only_tasks.md` als kleines
Folgepaket nach Run QU fort: Ein weiterer Runtime-Katalog-ID-Guard wird aus dem
semantischen Badge-Iterationspfad entfernt. Die Reduktion der teuren
Validierungsrunden für einfache linke Kreisarme soll nicht mehr an `AC0812`,
sondern an die bereits abgeleitete Connector-Geometrie gekoppelt sein.

## Umsetzung

- `runSemanticBadgeIterationImpl(...)` erkennt einfache linke Arm-Badges jetzt
  über `arm_enabled=True`, `connector_direction="left"` und `draw_text=False`.
- Der bisherige `AC0812`-Namensvergleich wurde entfernt; die Rundencap-Begründung
  lautet nun generisch `plain_left_arm_single_round`.
- Ein neutraler Regressionstest mit `ZZ_NEUTRAL_LEFT_ARM` sichert, dass die
  Validierungsrunden ohne Katalog-ID auf `1` reduziert werden.
- Die Legacy-Ratchet-Baseline wurde nach der Entfernung des Namensguards von 331
  auf 330 Runtime-ID-Vorkommen abgesenkt.

## Laufzeit- und Akzeptanznachweis

```bash
python -m compileall -q src tests/detailtests/test_iteration_mode_runtime_helpers.py && python tools/check_no_new_image_id_hardcoding.py && pytest -q tests/detailtests/test_iteration_mode_runtime_helpers.py
```

Ergebnis: Exit `0`; der Ratchet meldet `330 legacy occurrences remain`, und der
gezielte Iteration-Mode-Testblock läuft mit `3 passed`.

## 5-Zeilen-Log

- **Getestet:** Compileall, Hardcoding-Ratchet und gezielte Iteration-Mode-Regressionen.
- **Ergebnis:** Exit `0`; `3 passed`, Ratchet jetzt `330`.
- **Blocker:** IDO-17 ist noch nicht abgeschlossen; weitere Runtime-Katalog-IDs bleiben in anderen Spezialpfaden.
- **Dokumentation:** IDO-17 dokumentiert den weiteren Baseline-Abbau und die parameterbasierte Validierungsrunden-Cap.
- **Nächster Schritt:** IDO-17 fortsetzen und weitere ID-spezifische Runtime-Guards in struktur-/beschreibungsgesteuerte Parameter überführen.
