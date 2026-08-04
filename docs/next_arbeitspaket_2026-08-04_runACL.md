# Nächstes Arbeitspaket – Kontextgebundenes Telemetrie-Alias-Gate Run ACL (2026-08-04)

Run ACL schließt an den versuchsspezifischen Artefaktnamen aus Run ACK an.
Ein Beleg enthielt zwar bereits Run-ID und Run-Attempt, der eigenständige
Checker prüfte diese Werte bislang aber nur auf ihr Format und nicht gegen den
Workflow-Kontext, in dem der Beleg konsumiert wird.

## 1) Erwartete Workflow-Identität

Das Prüfwerkzeug akzeptiert nun die optionalen Parameter
`--expected-workflow-run-id` und `--expected-workflow-run-attempt`. Sind sie
gesetzt, muss die im Beleg gespeicherte Identität exakt übereinstimmen. Damit
kann ein formal gültiger Beleg eines älteren Versuchs nicht versehentlich als
Nachweis für einen anderen Versuch verwendet werden.

## 2) CI-Verdrahtung

Der No-Override-Prüflauf übergibt dem Checker die bereits für die Aufzeichnung
gesetzten Werte aus `github.run_id` und `github.run_attempt`. Aufzeichnung,
Inhaltsprüfung und Artefaktname beziehen sich dadurch auf denselben konkreten
Workflow-Versuch.

## 3) Ergebnis

Helper- und Workflow-Strukturtests sichern sowohl abweichende Run-IDs als auch
abweichende Run-Attempts ab. Der Checker bleibt für lokale Bestandsprüfungen
ohne Kontextparameter rückwärtskompatibel; CI verwendet den strengeren,
kontextgebundenen Modus.
