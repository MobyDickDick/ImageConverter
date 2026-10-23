# Nächstes Arbeitspaket – Artefaktgebundenes Telemetrie-Alias-Gate Run ACO (2026-08-05)

Run ACO zieht die in Run ACN gehärtete Workflow-Kontextprüfung bis zur
konsumierten Artefaktidentität weiter. Ein Beleg konnte bereits seinen
veröffentlichten Artefaktnamen selbst ausweisen; der eigenständige Checker bekam
jedoch noch keinen erwarteten Artefaktnamen aus dem aufrufenden CI-Kontext.

## 1) Erwarteter Artefaktcontainer

`tools/check_optimization_telemetry_alias_verification.py` akzeptiert nun den
optionalen Parameter `--expected-verification-artifact-name`. Ist er gesetzt,
muss das Feld `verification_artifact_name` im Beleg exakt übereinstimmen. Die
bestehende deterministische Prüfung gegen Run-ID und Run-Attempt bleibt
unverändert erhalten, sodass ein Beleg sowohl intern konsistent als auch an den
konkret erwarteten Container gebunden ist.

## 2) CI-Verdrahtung

Der No-Override-Prüflauf berechnet denselben Artefaktnamen, der später beim
Upload verwendet wird, bereits im Prüfstep als `VERIFICATION_ARTIFACT_NAME` und
übergibt ihn an das Gate. Dadurch prüft CI vor dem Upload, dass der persistierte
Beleginhalt und der Workflow-Artefaktcontainer dieselbe Identität tragen.

## 3) Regressionstests

Helper- und CLI-Tests decken abweichende erwartete Artefaktnamen ab. Der
Workflow-Strukturtest sichert zusätzlich die neue Umgebungsvariable und den
Gate-Parameter, damit zukünftige Änderungen die Artefaktbindung nicht
versehentlich aus dem CI-Pfad entfernen.
