# Nächstes Arbeitspaket – Robustes Telemetrie-Alias-Verifikationsgate Run ACH (2026-08-03)

Run ACH härtet das in Run ACG eingeführte Verifikationsgate an seiner
Dateigrenze. Ein Administrations-/CI-Gate muss auch bei unvollständigen oder
beschädigten Belegen kontrolliert fehlschlagen, statt mit einem Python-Traceback
abzubrechen.

## 1) Kontrollierte Dokumentvalidierung

`tools/check_optimization_telemetry_alias_verification.py` liest Alias und
Verifikationsbeleg nun unabhängig voneinander. Fehlende beziehungsweise nicht
lesbare Dateien, ungültiges JSON und JSON-Wurzeln, die keine Objekte sind,
werden als Gate-Abweichungen gesammelt. Sind beide Dokumente fehlerhaft, zeigt
ein einziger Lauf beide Ursachen.

Die bereits bestehende strikte Bindungs- und Erfolgsprüfung läuft unverändert,
sobald beide Dokumente syntaktisch gültige JSON-Objekte sind.

## 2) Stabiles CLI-Ergebnis

Für Dokumentfehler gilt derselbe Vertrag wie für eine Provenienzabweichung:
Das Tool schreibt `Telemetry alias verification: FAIL`, listet die konkreten
Ursachen auf und beendet sich mit Exitcode `1`. JSON-Syntaxfehler enthalten
Zeile und Spalte, aber keinen instabilen Traceback.

## 3) Ergebnis

Das eigenständige Verifikationsgate ist damit auch gegen typische
Artefakt-/Transportfehler abgesichert und kann ohne zusätzliche Exception-Hülle
in CI- und Administrationsskripten verwendet werden. Die tatsächliche
Alias-Aktivierung und externe Workflow-Ausführung bleiben administrative
Vorgänge.
