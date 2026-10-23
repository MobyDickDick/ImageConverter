# Nächstes Arbeitspaket – Maschinenlesbarer Telemetrie-Alias-Prüfbefehl Run ACE (2026-08-03)

Run ACE vervollständigt das ausführbare Aktivierungsrezept aus Run ACD: Neben
den beiden Befehlen zum Setzen der Repository-Variablen enthält das
Alias-Manifest nun auch den unmittelbar anschließenden, shell-sicheren
No-Override-Prüfbefehl.

## 1) Ausführbarer Prüfbefehl im Manifest

`recommended-baseline-alias.json` schreibt den neuen Schlüssel
`verification_command`. Der darin enthaltene `gh workflow run`-Befehl verwendet
die validierten Shard-Grenzen der Promotion und setzt
`promote_baseline=false`. Shard-Werte werden bereits beim Manifestbau mit
`shlex.quote` geschützt. Die strukturierte Abbildung `verification_dispatch`
bleibt parallel für API-basierte Automatisierungen erhalten.

## 2) Eine Quelle für Manifest und Summary

Die Promotion-Summary baut den Prüfbefehl nicht länger ein zweites Mal aus den
Einzelfeldern zusammen, sondern zeigt direkt `verification_command` aus dem
hochgeladenen Alias-Manifest an. Damit können maschinelle Verarbeitung und
Copy-and-paste-Aktivierung nicht durch abweichende Befehlsbildung auseinander
laufen.

## 3) Ergebnis und nächster Schritt

Das versionierte Promotion-Artefakt enthält jetzt die komplette ausführbare
Sequenz aus Alias-Aktivierung und No-Override-Verifikation. Repositoryseitig
bleibt als sinnvoller Folgepunkt nur eine optionale Automatisierung für das
Protokollieren der extern ausgeführten Workflow-Run-ID und ihres Gate-Status;
die tatsächliche Ausführung benötigt weiterhin Administratorrechte.
