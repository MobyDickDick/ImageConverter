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
