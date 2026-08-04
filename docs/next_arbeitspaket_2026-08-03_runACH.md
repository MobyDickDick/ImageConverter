# Nächstes Arbeitspaket – Automatischer Telemetrie-Alias-Beleg Run ACH (2026-08-03)

Run ACH bindet das in Run ACG eingeführte Verifikationsgate direkt in den
No-Override-Prüflauf ein. Ein erfolgreicher Alias-Test erzeugt damit seinen
Beleg ohne manuelle Übertragung von Workflow-Run-ID oder Gate-Status.

## 1) Beleg erst nach bestandenem Gate

Der Job `strict-converter-call` erzeugt
`telemetry-alias-verification.json` erst, nachdem das Vergleichsartefakt den
Status `passed` ausgewiesen hat. Als Verifikations-Run-ID wird unmittelbar
`github.run_id` verwendet; der Status wird in diesem ausschließlich grünen Pfad
als `passed` festgehalten. Schlägt die Konvertierung oder das Qualitätsgate fehl,
wird deshalb kein irreführender positiver Beleg veröffentlicht.

## 2) Selbstprüfung und langlebiges Artefakt

Direkt nach dem Schreiben prüft
`tools/check_optimization_telemetry_alias_verification.py` den Beleg gegen das
im heruntergeladenen Baseline-Artefakt enthaltene
`recommended-baseline-alias.json`. Nur wenn diese Bindungsprüfung besteht, lädt
der Workflow den Beleg als laufbezogen benanntes Artefakt mit 30 Tagen
Aufbewahrung hoch.

## 3) Ergebnis

Der administrative No-Override-Dispatch ist nun selbstbelegend: Ein grüner Lauf
liefert neben den Gate-Reports einen geprüften, maschinenlesbaren Nachweis für
genau den verwendeten Baseline-Alias. Negative oder abgebrochene Läufe können
weiterhin mit dem Werkzeug aus Run ACF explizit zu Diagnosezwecken protokolliert
werden.
=======
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
