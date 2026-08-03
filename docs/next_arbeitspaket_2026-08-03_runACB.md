# Nächstes Arbeitspaket – Aktivierbarer Telemetrie-Baseline-Alias Run ACB (2026-08-03)

Run ACB arbeitet den in Run ACA dokumentierten nächsten Schritt soweit
repositoryseitig automatisierbar ab: Jede neue Promotion erzeugt jetzt die
exakten Werte, mit denen der empfohlene Baseline-Alias gemeinsam weitergeschaltet
wird.

## 1) Maschinenlesbares Aktivierungsmanifest

`tools/build_optimization_telemetry_baseline_alias.py` leitet aus der bereits
geprüften Promotion-Provenienz die Run-ID und den versionierten Artefaktnamen ab.
Das resultierende `recommended-baseline-alias.json` enthält beide
Repository-Variablen als untrennbares Wertepaar und liegt im promoteten Artefakt.
Ungültige Run-IDs, Run-Attempts oder Provenienz-Schemata werden abgelehnt.

## 2) Sichtbares Übergabesignal

Der Promotion-Job schreibt dieselben beiden Werte in die GitHub-Step-Summary.
Damit muss ein Repository-Administrator keine Namen aus Logs zusammensetzen und
kann beide Variablen kontrolliert gemeinsam aktualisieren. Schreibrechte auf
Repository-Einstellungen werden dem Workflow bewusst nicht erteilt; die
eigentliche Aktivierung bleibt eine explizite administrative Freigabe.

## 3) Ergebnis und nächster Schritt

Der Alias-Übergabepunkt ist reproduzierbar und testbar. Nach der ersten echten
Promotion kann ein Administrator die beiden in der Summary ausgewiesenen Werte
setzen und den Workflow ohne manuelle Overrides starten. Dieser externe Lauf
kann anschließend mit Run-ID, Artefaktname und Gate-Status dokumentiert werden.
