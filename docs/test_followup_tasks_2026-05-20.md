# Test-Follow-up-Aufgaben (nur echte Grün-Tests in der Kernliste)

Datum: 2026-05-20  
Basis: letzter vollständiger grüner Suite-Lauf mit Python 3.10 (`pytest -q`).

## Session-Update 2026-05-21 (nicht-grüner Lauf explizit nachgeführt)

- Reproduzierter Kontrolllauf: `timeout 300 python -m pytest -q`
- Ergebnis: Lauf erreichte in 300s kein finales `pytest`-Summary und endete mit Exit `124` (Timeout), bei sichtbarem Zwischenstand mit weiterhin vorhandenen `xfailed` (`x`) und `skipped` (`s`) Markern.
- Einordnung: Dieser Lauf zählt **nicht** als „wirklich grün“ und bleibt als Follow-up-Aufgabe offen.

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


### A5 – Laufzeitüberschreitungen strikt als Follow-up-Aufgaben behandeln
- [ ] Alle Testfälle mit Laufzeitüberschreitung (`_PerTestTimeout`) täglich aus dem `pytest`-Output extrahieren und in einer eigenen Liste erfassen (NodeID + Dauergrenze).
- [ ] Für jeden Timeout-Fall genau **eine** Folgeaufgabe mit Akzeptanzkriterium anlegen (z. B. „<30s in Python 3.10.20“).
- [ ] Timeout-Fälle dürfen nicht als „nur Umgebung langsam“ verbucht werden; sie gelten bis zur Auflösung als offene Qualitätsaufgabe.
- [ ] Nach Stabilisierung: Timeout-Marker entfernen und Test zurück in `core-green` überführen.

### A6 – `pytest -q` in 300s wieder deterministisch zum Endsummary bringen
- [ ] Timeout-Lauf vom 2026-05-21 (`timeout 300 python -m pytest -q`, Exit `124`) in Teilbatches aufspalten und den langsamsten Block identifizieren.
- [ ] Für den langsamsten Block einen reproduzierbaren Einzel-Repro (NodeID oder Marker-Subset) dokumentieren.
- [ ] Akzeptanz: Ein erneuter Suite-Lauf mit identischem 300s-Limit endet mit finalem `pytest`-Summary statt Exit `124`.

## Definition „wirklich grün“

Ein Test zählt nur als **wirklich grün**, wenn er:
1. ausgeführt wurde,
2. `passed` ist,
3. nicht `skip`/`xfail`/`deselect` ist,
4. und keine Warnung erzeugt (für das Kernprofil).
