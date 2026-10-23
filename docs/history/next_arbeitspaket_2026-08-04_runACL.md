# Nächstes Arbeitspaket – Selbstbeschreibendes Telemetrie-Alias-Artefakt Run ACL (2026-08-04)

Run ACL schließt die nach Run ACK verbliebene Prüflücke zwischen dem
versuchsspezifischen Upload-Namen und dem Inhalt des Verifikationsbelegs. Der
Workflow benannte das Artefakt bereits eindeutig, der heruntergeladene Beleg
konnte seinen erwarteten Artefaktnamen bislang jedoch nicht selbst ausweisen.

## 1) Artefaktidentität im Belegvertrag

Der Belegvertrag liegt nun in Version
`optimization_render_telemetry_alias_verification_v4` vor. Das Feld
`verification_artifact_name` wird deterministisch aus Workflow-Run-ID und
Workflow-Versuch gebildet. Damit enthält der Beleg neben seiner inhaltlichen
Provenienz auch die Identität des Containers, unter der er veröffentlicht wird.

## 2) Strikte Konsistenzprüfung

Das eigenständige Verifikationsgate berechnet den erwarteten Artefaktnamen
erneut und vergleicht ihn mit dem persistierten Feld. Ein umbenannter Beleg, ein
Beleg aus einem anderen Versuch oder eine nachträglich manipulierte
Artefaktidentität führen kontrolliert zu `FAIL`. Der Workflow-Strukturtest
sichert weiterhin, dass der Upload dasselbe Namensschema verwendet.

## 3) Ergebnis

Run-ID, Versuch, Beleginhalt und Upload-Name bilden nun einen gemeinsam
prüfbaren Vertrag. Ein heruntergeladener positiver Nachweis kann ohne Wissen
über den ursprünglichen Workflow-Aufbau seinem deterministischen
Artefaktcontainer zugeordnet werden.
## 4) Kontextgebundenes Telemetrie-Alias-Gate

Run ACL schließt außerdem an den versuchsspezifischen Artefaktnamen aus Run ACK an.
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
