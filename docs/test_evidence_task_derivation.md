# Regeln zur Ableitung von Aufgaben aus Test-Evidence

Diese Richtlinie trennt beobachtete Unterprozess-Ergebnisse von dem
maßgeblichen Abschlussurteil. Sie gilt für manuelle Auswertungen und für
Ausgaben von `tools/aggregate_test_evidence.py`.

## 1. Entscheidungsregeln

Ein einzelnes `Verdict: FAIL` eröffnet **nicht automatisch** eine
Produkt-Korrekturaufgabe. Für jeden Evidence-Eintrag werden zuerst
`Expectation`, Szenario-ID und anschließend das Abschlussprofil ausgewertet:

| Evidence-Zustand | Einordnung | Abgeleitete Aufgabe |
|---|---|---|
| `Verdict: FAIL`, `Expectation: MET` | Erwarteter Negativpfad ist abgedeckt. | Keine Produkt-Korrekturaufgabe. |
| Beliebiges `Verdict`, `Expectation: UNMET` | Beobachtung widerspricht der definierten Erwartung. | Produkt-Korrekturaufgabe für das betroffene Szenario. |
| `Verdict: PASS`, `Expectation: NOT_SPECIFIED` | Regulärer Positivpfad ist grün. | Keine Korrekturaufgabe. |
| `Verdict: FAIL`, `Expectation: NOT_SPECIFIED` | Unerwarteter Einzelfehler; das Abschlussprofil entscheidet über den Release-/Produktstatus. | Bei rotem oder fehlendem Abschlussprofil Produkt-Korrekturaufgabe; andernfalls als Roh-Evidenz untersuchen, aber nicht isoliert zum Release-Blocker erklären. |
| Abschlussprofil fehlt oder ist rot | Maßgebliches Gesamturteil ist `FAIL`. | Produkt-Korrekturaufgabe erzeugen. |
| Abschlussprofil ist grün | Maßgebliches Gesamturteil ist `PASS`. | Keine Produkt-Korrekturaufgabe allein aufgrund erwarteter roter Unterprozesse. |

Das maßgebliche Abschlussprofil ist standardmäßig das Szenario
`completion-profile`. Ein anderes Profil muss beim Aggregieren explizit mit
`--completion-scenario` angegeben werden.

## 2. Regeln für erwartete Negativtests

Erwartete Negativtests müssen ihren beobachteten Fehler unverändert
protokollieren: `Verdict: FAIL` und der tatsächliche Exit-Code bleiben
auditierbar. `Expectation: MET` kennzeichnet separat, dass genau dieses
Ergebnis erwartet wurde.

Für einen erwarteten Negativtest wird nur dann eine
**Evidence-Korrekturaufgabe** eröffnet, wenn seine Metadaten die Auswertung
nicht zuverlässig erlauben. Dazu zählen insbesondere:

- fehlende oder nicht stabile Szenario-ID,
- fehlender Testkontext bei nicht selbsterklärenden Szenarien,
- fehlender Korrelationsschlüssel für zusammengehörige Mehrschritt-Gates,
- fehlende Erwartungsangabe oder widersprüchliche Kombinationen aus
  erwartetem Exit-Code und `Expectation`,
- fehlender Exit-Code, Logpfad oder Git-Bezug,
- mehrere ununterscheidbare Einträge für dasselbe Szenario.

Solche Metadatenfehler betreffen die Evidence-Erzeugung oder -Aggregation,
nicht automatisch den vom Negativtest ausgeführten Produktpfad.

## 3. Minimale Schablone für echte Produkt-Korrekturaufgaben

Jede echte Produkt-Korrekturaufgabe enthält mindestens:

```markdown
# Korrekturaufgabe: <kurzer Titel>

- Symptom: <beobachtetes Fehlverhalten>
- Szenario-ID: <stabile ID>
- Reproduktionsbefehl: `<vollständiger Befehl>`
- Erwartetes Ergebnis: <fachlich oder technisch erwartetes Ergebnis>
- Tatsächlicher Exit-Code: <Code oder "missing">
- Logpfad: `<Pfad zum Evidence-Log>`
- Git-SHA: `<geprüfter Stand>`
- Akzeptanztest: <konkreter Test und eindeutig grünes Ergebnis>
```

Zusätzliche Diagnoseinformationen sind willkommen, ersetzen aber keines der
Pflichtfelder. Der Reproduktionsbefehl und der Akzeptanztest müssen so konkret
sein, dass eine Folgesession die Aufgabe ohne Interpretation temporärer
Dateipfade erneut prüfen kann.

## 4. Empfohlener Auswertungsablauf

1. Einzel-Summaries mit `tools/run_test_evidence.sh` erzeugen und erwartete
   Negativpfade über `--expected-exit` kennzeichnen.
2. Szenario-ID, Testkontext und gegebenenfalls Run-ID auf Vollständigkeit und
   Widerspruchsfreiheit prüfen.
3. Roh-Evidenz mit `tools/aggregate_test_evidence.py` aggregieren.
4. Das Gesamturteil ausschließlich aus dem konfigurierten Abschlussprofil
   übernehmen.
5. Eine Produkt-Korrekturaufgabe nur bei `Expectation: UNMET` oder einem
   fehlenden/roten Abschlussprofil eröffnen.
6. Bei erwarteten Negativpfaden ausschließlich Metadatenprobleme als
   Evidence-Korrekturaufgaben übernehmen.

Beispiel:

```bash
python tools/aggregate_test_evidence.py \
  --output artifacts/test-evidence/aggregate.md \
  --json-output artifacts/test-evidence/aggregate.json \
  --correction-task artifacts/test-evidence/completion-correction-task.md \
  artifacts/test-evidence/*-summary.md
```

Ein grünes `completion-profile` führt dabei zu `overall_verdict=PASS`, auch
wenn davor erwartete Negativpfade mit `Verdict: FAIL` und
`Expectation: MET` aufgeführt sind.
