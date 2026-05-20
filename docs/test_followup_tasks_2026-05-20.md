# Test-Follow-up-Aufgaben (nur echte Grün-Tests in der Kernliste)

Datum: 2026-05-20  
Basis: letzter vollständiger grüner Suite-Lauf mit Python 3.10 (`pytest -q`).

## Ziel

Nur **wirklich grüne** Tests sollen als stabile Kern-Testliste gelten.  
Alles andere (skip/deselect/xfail/warnings) wird hier als explizite Aufgabe geführt.

## Snapshot (Ist-Stand)

- `842 passed`
- `4 skipped`
- `18 deselected`
- `3 xfailed`
- `5 warnings`

## Aufgaben aus Nicht-Grün-Ergebnissen

### A1 – Skipped-Tests eliminieren oder eindeutig als optionale Fixture-Tests markieren
- [ ] Alle 4 `skipped` Tests identifizieren und je Test entscheiden:
  - [ ] Entweder Fixture/Umgebung in CI bereitstellen (damit Test wieder grün läuft),
  - [ ] oder Test dauerhaft in eine klar benannte optional-suite verschieben (`@pytest.mark.optional_fixture`).
- [ ] Für jeden Skip-Grund eine reproduzierbare Anleitung in `docs/` ergänzen.

### A2 – Deselected-Tests in explizite Testprofile überführen
- [ ] Die 18 `deselected` Tests namentlich erfassen.
- [ ] In `pytest.ini`/Runner-Skripten feste Profile definieren:
  - [ ] `core-green` (nur harte grüne Tests),
  - [ ] `extended` (inkl. langsam/optional),
  - [ ] `research` (experimentell).
- [ ] Sicherstellen, dass `core-green` keine impliziten Deselections mehr enthält.

### A3 – XFail-Tests in echte Qualitäts-Tasks auflösen
- [ ] Alle 3 `xfailed` Tests inkl. Grund dokumentieren.
- [ ] Für jeden `xfail` ein Akzeptanzkriterium definieren, wann zurück auf normalen Assert.
- [ ] Ziel: `xfail` schrittweise auf `0` reduzieren.

### A4 – Warnings auf Null bringen (oder strikt erlaubte Liste pflegen)
- [ ] Die 5 Warnungen (aktuell `SwigPyPacked/SwigPyObject/swigvarlink` Deprecations) technisch bewerten.
- [ ] Entweder:
  - [ ] Ursache beheben (Abhängigkeiten/Bindings aktualisieren), oder
  - [ ] temporär als bekannte, explizit erlaubte Warnungen dokumentieren.
- [ ] Mittelfristig CI-Profil mit `-W error` für `core-green` vorbereiten.

## Definition „wirklich grün“

Ein Test zählt nur als **wirklich grün**, wenn er:
1. ausgeführt wurde,
2. `passed` ist,
3. nicht `skip`/`xfail`/`deselect` ist,
4. und keine Warnung erzeugt (für das Kernprofil).

