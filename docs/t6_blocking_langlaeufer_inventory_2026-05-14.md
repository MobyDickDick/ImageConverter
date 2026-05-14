# T6 Blocking-Langläufer Inventar (Session 2026-05-14)

## Anlass
T6 verlangt die Identifikation aktuell blockierender Langläufer-Tests sowie eine priorisierte Abbau-Reihenfolge.

## Primäraufgabe (T6): Inventarisierung aus vorhandenen Laufartefakten

Quelle/Methodik:
- Log-Sichtung über bestehende T5- und Vollbereichs-Artefakte.
- Fokus auf (a) wiederholte Timeout-/Exit-124-Pfade im AC08-Batch und (b) historisch auffällige T5-Tests.

### Befunde
1. **Hauptblocker bleibt der Vollbereichs-Batch `AC0800..AC0899` (N1/N2-Pfad)**
   - Wiederholte Timeout-Exits `124` in den jüngsten Runs (`runDA`, `runDB`, `runDC`).
   - Blockade ist kumulative Laufzeit, nicht ein einzelner reproduzierbarer Unit-Test-Fehler.

2. **Historischer T5-Failure ist aktuell nicht mehr persistent**
   - Das früher markierte `test_global_search_skips_deterministic_track_after_strong_stochastic_gain` war in älteren Logs einmal als `FAILED` sichtbar.
   - In der Plan-B-Session-Reproduktion (siehe unten) läuft der Test aktuell `PASS`.

3. **OpenCV/Numpy-Import-Hinweis ist weiterhin ein Umgebungsrisiko**
   - In früheren Runs (v. a. falsche Python-Umgebung) führte das zu „Exit 0 ohne Variantenfortschritt“.
   - Für priorisierte Langläuferdiagnose muss die bestätigte Python-3.10-Toolchain genutzt werden.

## Priorisierte Abbau-Reihenfolge (T6)
1. **Priorität P1:** N1/N2-Batchlaufzeit weiter reduzieren (größter Hebel auf Gesamt-Blockade).
2. **Priorität P2:** Einzelpfad-Regressionen nur noch bei erneuter Reproduzierbarkeit hochstufen.
3. **Priorität P3:** Umgebungsfehler (OpenCV/Numpy) per Guardrails früh abfangen, damit keine „leeren“ Runs entstehen.

## Plan-B-Aufgabe (T6-PB): Schneller Einzeltest-Repro statt Langlauf

Ziel: Wenn T6 keine neue sofortige Langlauf-Maßnahme liefert, mindestens einen historischen Blocker-Test schnell verifizieren.

Ausführung:
- `pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`

Ergebnis:
- Exit `0`, `1 passed in 0.18s`.
- Damit ist der historische Einzeltest aktuell **nicht** als aktiver Blocker einzustufen.

## Kurzfazit
T6 liefert für den aktuellen Stand keinen neuen unit-test-basierten Hard-Blocker; der dominierende Engpass bleibt die kumulative Laufzeit im Vollbereichspfad. Die gekoppelte Plan-B-Aufgabe wurde erfolgreich abgeschlossen und bestätigt, dass der frühere Einzeltest-Fehler derzeit nicht reproduzierbar ist.
