# Korrekturaufgaben aus der Test-Evidence-Auswertung (2026-06-13)

## Ausgangslage

Die Auswertung gehört zu Git-SHA
`5feafca22f4da385bdec77f60bf0beebb6d2f7d2` auf `refs/heads/main`.
Der abschließende Eintrag `completion-profile` ist mit Exit-Code `0` grün.
Die davor aufgeführten roten Einträge stammen aus Negativpfaden der
Detailtests für den Evidence-Wrapper und das FP-D12-Release-Kandidaten-Gate:

- `unit-fail` mit Exit-Code `3` prüft, dass ein fehlgeschlagener Unterbefehl als
  `FAIL` protokolliert und sein Exit-Code weitergegeben wird.
- `FP-D12 ac08-smoke` mit Exit-Code `7` prüft eine akzeptierte Ausnahme.
- `FP-D12 ac08-smoke` mit Exit-Code `5` prüft einen nicht akzeptierten Blocker.
- `FP-D12 ac08-smoke` mit Exit-Code `124` und das nachfolgende
  `quality-gate` mit Exit-Code `1` prüfen den Timeout-Pfad sowie den Schutz vor
  veralteten Erfolgsmessungen.
- Der zuletzt aufgeführte vollständige FP-D12-Dreischritt ist grün.

Damit belegt die vorliegende Auswertung **keinen Produktfehler**. Sie zeigt
stattdessen, dass erwartete Negativ-Evidenz in der zusammengeführten Ausgabe
wie ein realer Abschlussfehler aussieht. Die Korrekturaufgaben betreffen daher
die Eindeutigkeit und Auswertbarkeit der Test-Evidence.

## Abgeleitete Korrekturaufgaben

### TE-K1 – Erwarteten Negativpfad explizit kennzeichnen

- [x] `tools/run_test_evidence.sh` um die maschinenlesbare Erwartungsangabe
  `--expected-exit CODE` ergänzen.
- [x] Neben dem beobachteten `Verdict` ein separates Ergebnis der
  Erwartungsprüfung als `Expectation: MET`, `UNMET` oder `NOT_SPECIFIED`
  ausgeben.
- [x] Der Wrapper dokumentiert weiterhin den beobachteten Exit-Code; ein
  erwartetes Unterkommando-`FAIL` darf nicht nachträglich als beobachtetes
  `PASS` umetikettiert werden.
- [x] Detailtests für erwarteten Exit-Code, unerwartetes Grün und unerwarteten
  abweichenden Fehlercode ergänzen.

**Umgesetzt am 2026-06-13:** Der Wrapper validiert erwartete Exit-Codes im
Bereich `0..255`, schreibt Erwartung und Erwartungsergebnis in jedes Summary
und gibt unabhängig davon weiterhin den tatsächlich beobachteten Exit-Code
zurück.

**Akzeptanzkriterium:** Ein Mensch und ein Parser können unterscheiden, ob
`Verdict: FAIL` einen absichtlich getesteten Negativpfad oder einen Fehler des
übergeordneten Testlaufs bezeichnet.

### TE-K2 – Evidence-Einträge mit Testkontext und eindeutiger Identität versehen

- [x] In jedem Summary-Eintrag mindestens die erzeugende Pytest-NodeID oder
  eine stabile Szenario-ID protokollieren.
- [x] Wiederholte Anzeigenamen wie `FP-D12 core-suite`, `FP-D12 ac08-smoke`
  und `FP-D12 quality-gate` um das Szenario ergänzen, beispielsweise
  `accepted-exception`, `unaccepted-blocker`, `stale-metrics-timeout` und
  `path-propagation`.
- [x] Optional einen Lauf-/Korrelationsschlüssel ausgeben, damit die drei
  Schritte eines Gate-Szenarios eindeutig zusammengehören.

**Umgesetzt am 2026-06-13:** Der Evidence-Wrapper schreibt nun `Scenario ID`,
`Test context` und `Run ID`. Das FP-D12-Gate ergänzt die Szenario-ID in jedem
Anzeigenamen und reicht einen gemeinsamen Korrelationsschlüssel an alle drei
Gate-Schritte weiter. Die vier Detailtests setzen die stabilen Szenarien
`accepted-exception`, `unaccepted-blocker`, `stale-metrics-timeout` und
`path-propagation`.

**Akzeptanzkriterium:** Die vier FP-D12-Szenarien lassen sich ohne Auswertung
temporärer Dateipfade eindeutig gruppieren und den zuständigen Detailtests
zuordnen.

### TE-K3 – Roh-Evidenz und Abschlussurteil getrennt aggregieren

- [ ] Die Sammelausgabe in die Bereiche `Scenario evidence` und
  `Completion verdict` gliedern.
- [ ] Das Gesamturteil ausschließlich aus dem übergeordneten
  `completion-profile` beziehungsweise einem expliziten Aggregatstatus
  ableiten.
- [ ] Erwartete Negativpfade als abgedeckte Szenarien zählen, nicht als offene
  Produktblocker.
- [ ] Bei einem roten `completion-profile` weiterhin automatisch eine echte
  Korrekturaufgabe mit Logpfad, Exit-Code, Git-SHA und reproduzierbarem
  Startbefehl erzeugen.

**Akzeptanzkriterium:** Für die vorliegende Evidenz lautet das maschinenlesbare
Gesamturteil `PASS`; zugleich bleiben alle beobachteten Unterprozess-Exit-Codes
unverändert und auditierbar erhalten.

### TE-K4 – Dokumentierte Regeln für die Aufgabenableitung ergänzen

- [ ] In der Test-/Release-Dokumentation festhalten, dass ein einzelner
  `Verdict: FAIL` nur dann eine Produkt-Korrekturaufgabe eröffnet, wenn die
  Erwartung nicht erfüllt wurde oder das Abschlussprofil rot ist.
- [ ] Für echte Fehler eine minimale Aufgabenschablone definieren:
  Symptom, Szenario-ID, Reproduktionsbefehl, erwartetes Ergebnis, tatsächlicher
  Exit-Code, Logpfad und Akzeptanztest.
- [ ] Für erwartete Negativtests festlegen, dass lediglich fehlende oder
  widersprüchliche Metadaten als Evidence-Korrekturaufgabe gelten.

**Akzeptanzkriterium:** Eine erneute Auswertung derselben Daten erzeugt die
Evidence-Aufgaben TE-K1 bis TE-K4, aber keine irreführende Aufgabe zur
Reparatur von `ac08-smoke` oder `quality-gate`.

## Priorisierung

1. **TE-K1** – verhindert die fachlich falsche Interpretation absichtlicher
   Fehlerpfade.
2. **TE-K2** – beseitigt die Mehrdeutigkeit der wiederholten FP-D12-Namen.
3. **TE-K3** – macht die automatische Gesamtbewertung robust.
4. **TE-K4** – sichert die Regel dauerhaft für manuelle und automatisierte
   Folgeauswertungen.

## Nicht als Korrekturaufgabe übernommen

- Die grünen Einträge `unit-pass`, `FP-D12 core-suite`, `FP-D12 quality-gate`
  und der vollständige grüne FP-D12-Lauf benötigen keine Reparatur.
- Die Exit-Codes `3`, `7`, `5`, `124` und `1` werden nicht isoliert als
  Produktdefekte übernommen, weil sie in den Detailtests gezielt erzeugte
  Negativszenarien dokumentieren.
- Für den geprüften Stand wird kein Release-Blocker eröffnet, da das
  `completion-profile` am 13. Juni 2026 um 16:34:26 UTC mit Exit-Code `0`
  abgeschlossen wurde.
