# Nächstes Arbeitspaket – Empfohlener Telemetrie-Baseline-Alias Run ACA (2026-08-03)

Run ACA setzt den in Run ABZ dokumentierten Folgepunkt um: Der manuelle
Telemetrie-Gate-Workflow kann eine zentral empfohlene Baseline verwenden, ohne
dass deren Run-ID und Artefaktname bei jedem Aufruf erneut eingetragen werden
müssen.

## 1) Repository-Variablen als Alias

Die Repository-Variablen
`OPTIMIZATION_RENDER_TELEMETRY_BASELINE_RUN_ID` und
`OPTIMIZATION_RENDER_TELEMETRY_BASELINE_ARTIFACT_NAME` bilden gemeinsam den
Alias auf die aktuell empfohlene, bereits promotete Baseline. Die manuellen
Workflow-Eingaben bleiben als optionale, paarweise zu verwendende Overrides
erhalten. Damit kann die Empfehlung zentral weitergeschaltet werden, während
gezielte Rechecks weiterhin eine ältere freigegebene Version auswählen können.

## 2) Frühe Konsistenzprüfung

Vor dem Artefakt-Download verlangt der Workflow eine positive numerische Run-ID
und einen versionierten Artefaktnamen desselben Laufs. Anschließend bleibt die
vollständige Provenienz- und Shard-Prüfung aus Run ABZ aktiv. Ein fehlender oder
nur halb gepflegter Alias bricht daher mit einer verständlichen Meldung ab,
statt implizit ein beliebiges Artefakt zu verwenden.

## 3) Aufgabenstand und nächster Schritt

Dieses Anschlussstück ist kein eigener Checkbox-Eintrag in
`docs/open_tasks.md`. Nach der dort dokumentierten Zählregel bleiben deshalb
`401` Aufgaben insgesamt, `374` erledigt und `27` offen. Weniger als `27` sind
es erst, wenn mindestens eine der offenen Checkboxen fachlich abgeschlossen,
mit einem Testsignal dokumentiert und von `- [ ]` auf `- [x]` gesetzt wird
(oder wenn eine nachweislich nicht mehr relevante Checkbox begründet aus dem
Backlog entfernt wird). Das bloße Abarbeiten eines dokumentierten Folgepunkts
ohne eigene Checkbox verändert den Zähler nicht.

Als nächstes kann eine tatsächlich promotete Baseline als Repository-Alias
eingetragen und der Workflow einmal ohne manuelle Baseline-Overrides ausgeführt
werden. Nach einer späteren Promotion müssen beide Variablen gemeinsam auf die
neue Run-ID und den neuen versionierten Artefaktnamen aktualisiert werden.
