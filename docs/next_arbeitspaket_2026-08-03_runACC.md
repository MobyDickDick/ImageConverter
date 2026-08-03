# Nächstes Arbeitspaket – Telemetrie-Alias-Aktivierungscheck Run ACC (2026-08-03)

Run ACC arbeitet den nach Run ACB repositoryseitig noch offenen Teil des
Aktivierungsschritts ab: Das Promotion-Artefakt beschreibt nun nicht nur die
beiden gemeinsam zu setzenden Repository-Variablen, sondern auch den exakten
anschließenden Prüflauf ohne manuelle Baseline-Overrides.

## 1) Reproduzierbarer Prüflauf

`recommended-baseline-alias.json` enthält einen `verification_dispatch` mit
Workflow-Datei, ursprünglichen Shard-Grenzen und deaktivierter erneuter
Promotion. Dadurch bleibt der Prüflauf auf demselben Katalogausschnitt wie die
promotete Baseline und löst die Baseline ausschließlich über den gerade
aktivierten Repository-Alias auf.

Die Promotion-Summary zeigt aus diesen maschinenlesbaren Angaben zusätzlich
einen vollständigen `gh workflow run`-Befehl. Ein Administrator kann damit nach
dem gemeinsamen Setzen der Variablen den vorgesehenen Aktivierungscheck ohne
erneutes Zusammensetzen der Eingaben starten.

## 2) Frühe Provenienzprüfung

Der Manifest-Builder akzeptiert Shard-Anfang und -Ende nur noch als nicht leere
Strings. Ungenügende Promotion-Provenienz kann daher kein scheinbar
ausführbares Aktivierungsrezept erzeugen. Helper-Tests sichern sowohl den
Dispatch-Vertrag als auch die neuen Fehlerfälle.

## 3) Ergebnis und nächster Schritt

Der repositoryseitig automatisierbare Aktivierungspfad ist vollständig:
Promotion, Variablen-Wertepaar und passender No-Override-Prüflauf werden in
einem Artefakt übergeben. Extern offen bleibt die administrative Aktivierung
einer real promoteten Baseline und die Dokumentation der erfolgreichen
Workflow-Run-ID samt Gate-Status.
