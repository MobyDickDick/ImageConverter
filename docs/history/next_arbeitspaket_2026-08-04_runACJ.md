# Nächstes Arbeitspaket – Versuchssicherer Telemetrie-Alias-Beleg Run ACJ (2026-08-04)

Run ACJ ergänzt die Revisionsbindung aus Run ACI um die noch fehlende
Unterscheidung von GitHub-Workflow-Wiederholungen. Ein erneut ausgeführter
Workflow behält seine Run-ID, besitzt aber einen eigenen Run-Attempt und darf
deshalb keinen mehrdeutigen Verifikationsbeleg erzeugen.

## 1) Run-Attempt als Pflichtfeld

Der Belegvertrag liegt nun in Version
`optimization_render_telemetry_alias_verification_v3` vor. Neben der positiven
Workflow-Run-ID verlangt er den ebenfalls positiven
`verification_workflow_run_attempt`. Erzeuger und eigenständiges Prüfwerkzeug
lehnen fehlende, boolesche, nullwertige oder negative Versuchsnummern ab.

## 2) Eindeutige Workflow-Artefakte

Der No-Override-Prüflauf übergibt `github.run_attempt` direkt an das
Aufzeichnungswerkzeug. Auch der Name des hochgeladenen Belegartefakts enthält
Run-ID und Run-Attempt. Wiederholungen desselben GitHub-Laufs bleiben dadurch
getrennt abrufbar und ihr persistierter Inhalt weist die konkrete Ausführung
eindeutig aus.

## 3) Validierung

Helper-Tests sichern den v3-Vertrag, ungültige Versuchsnummern, die Prüfung
eines fehlenden Pflichtfelds und die Workflow-Verdrahtung ab. Die bestehende
Bindung an Alias, Shard, Gate-Status und Quellrevision bleibt unverändert.
