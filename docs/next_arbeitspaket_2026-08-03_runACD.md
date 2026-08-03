# Nächstes Arbeitspaket – Ausführbares Telemetrie-Alias-Aktivierungsrezept Run ACD (2026-08-03)

Run ACD schließt die letzte repositoryseitig automatisierbare Lücke des in Run
ACC vorbereiteten Aktivierungschecks: Das Promotion-Artefakt liefert nun neben
den Zielwerten auch direkt ausführbare Befehle zum gemeinsamen Umschalten des
empfohlenen Baseline-Alias.

## 1) Maschinenlesbare Aktivierungsbefehle

`recommended-baseline-alias.json` enthält unter `activation_commands` zwei
geordnet ausgeführte `gh variable set`-Befehle. Sie setzen die Run-ID und den
versionierten Artefaktnamen aus derselben validierten Promotion-Provenienz. Die
bereits vorhandene strukturierte Abbildung `repository_variables` bleibt für
andere Automatisierungen erhalten.

## 2) Copy-and-paste-fähige Workflow-Summary

Die Promotion-Summary zeigt die beiden Befehle gemeinsam in einem Bash-Block
und danach weiterhin den No-Override-Prüflauf. Shard-Werte werden beim Aufbau
des angezeigten Prüfbefehls Shell-sicher quotiert. Administratoren müssen damit
weder Variablennamen noch Werte oder Shard-Grenzen aus Freitext übertragen.

## 3) Ergebnis und nächster Schritt

Promotion, administrative Aktivierung und der anschließende Alias-Prüflauf
sind jetzt durch ein einziges versioniertes Manifest reproduzierbar verbunden.
Extern offen bleibt weiterhin nur das tatsächliche Ausführen der Befehle mit
Repository-Administratorrechten und das Festhalten der erfolgreichen
Workflow-Run-ID samt Gate-Status.
