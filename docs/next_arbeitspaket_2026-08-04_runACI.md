# Nächstes Arbeitspaket – Revisionsgebundener Telemetrie-Alias-Beleg Run ACI (2026-08-04)

Run ACI schließt eine Provenienzlücke im automatischen Alias-Beleg aus Run ACH:
Eine erfolgreiche Ausführung darf eine Baseline nur dann verifizieren, wenn der
Workflow auf genau der Revision läuft, aus der diese Baseline promotet wurde.

## 1) Verifikationsrevision als Pflichtfeld

Der Belegvertrag liegt nun in Version
`optimization_render_telemetry_alias_verification_v2` vor und enthält zusätzlich
`verification_source_sha`. Das Aufzeichnungswerkzeug verlangt den Wert explizit
und lehnt den Beleg bereits beim Erzeugen ab, wenn er nicht mit `source_sha` des
Baseline-Alias übereinstimmt.

## 2) Prüfung im Workflow und bei späterer Auswertung

Der erzeugte Prüfbefehl startet den No-Override-Workflow mit `--ref` auf der
promoteten Revision; der Workflow übergibt `github.sha` als tatsächliche
Verifikationsrevision. Das eigenständige Prüfwerkzeug vergleicht das persistierte
Feld erneut mit dem Alias, sodass auch eine nachträgliche Manipulation des
Artefakts zu einem kontrollierten `FAIL` führt. Tests decken Erzeugung,
CLI-Vertrag, Workflow-Verdrahtung und die negative Abweichung ab.

## 3) Ergebnis

Run-ID, Gate-Status, Baseline-Provenienz und die tatsächlich ausgeführte
Workflow-Revision sind nun gemeinsam maschinenlesbar gebunden. Ein Beleg aus
einer anderen Code-Revision kann nicht länger als erfolgreicher Nachweis für den
promoteten Alias ausgegeben werden.
