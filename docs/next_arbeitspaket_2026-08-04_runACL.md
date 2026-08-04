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
