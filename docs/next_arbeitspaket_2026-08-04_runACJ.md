# Nächstes Arbeitspaket – Versuchssicherer Telemetrie-Alias-Beleg Run ACJ (2026-08-04)

Run ACJ schließt die nach der Revisionsbindung aus Run ACI verbliebene
Identitätslücke bei erneut ausgeführten GitHub-Workflow-Läufen. Mehrere Versuche
desselben Laufs teilen sich eine Run-ID, können aber unterschiedliche Ergebnisse
haben. Ein Verifikationsbeleg muss deshalb auch den tatsächlich erfolgreichen
Versuch eindeutig benennen.

## 1) Workflow-Versuch als Pflichtfeld

Der Belegvertrag liegt nun in Version
`optimization_render_telemetry_alias_verification_v3` vor und enthält zusätzlich
`verification_workflow_run_attempt`. Das Aufzeichnungswerkzeug akzeptiert nur
positive ganzzahlige Versuchsnummern und verlangt den Wert sowohl in der
Python-API als auch über die CLI.

## 2) Automatische Erfassung und spätere Prüfung

Der No-Override-Workflow übergibt `github.run_attempt` gemeinsam mit
`github.run_id` und `github.sha` an das Aufzeichnungswerkzeug. Das eigenständige
Prüfgate validiert das persistierte Feld erneut und weist fehlende, boolesche,
nicht ganzzahlige oder nicht positive Werte kontrolliert zurück. Tests decken
Vertragsaufbau, negative Werte, CLI-Aufruf und Workflow-Verdrahtung ab.

## 3) Ergebnis

Ein positiver Alias-Beleg identifiziert jetzt Promotion, Code-Revision,
Workflow-Lauf und konkreten Ausführungsversuch. Ein später fehlgeschlagener oder
neu gestarteter Versuch derselben Run-ID kann dadurch nicht mit dem zuvor
verifizierten Lauf verwechselt werden.
