# Nächstes Arbeitspaket – Dauerhafter Telemetrie-Baseline-Kanal Run ABZ (2026-08-03)

Run ABZ setzt den in Run ABY dokumentierten nächsten Schritt um: Das strikte
Optimierungs-Telemetrie-Gate verwendet nicht mehr den im aktuellen Lauf erzeugten
Kandidaten als Vergleichsbasis, sondern eine explizit ausgewählte, bereits
promotete Baseline aus einem früheren Workflow-Lauf.

## 1) Expliziter Cross-Run-Kanal

Die manuellen Eingaben `baseline_run_id` und `baseline_artifact_name` benennen
den Quelllauf und den vollständigen versionierten Artefaktnamen. Der Gate-Job
lädt dieses Artefakt mit `actions/download-artifact` und einem expliziten
`run-id`; die Workflow-Berechtigungen bleiben auf lesenden Zugriff beschränkt.
Der im aktuellen Lauf aufgezeichnete Katalog-Shard bleibt ein Kandidat, der erst
nach einem erfolgreichen Vergleich optional promotet werden kann.

## 2) Provenienz- und Shard-Sicherung

Vor dem Konverteraufruf prüft der Workflow Schema und Mindestinhalt der Summary.
Zusätzlich müssen Quelllauf und Run-Attempt aus `provenance.json` exakt zum
Artefaktnamen passen. Auch `shard_start` und `shard_end` müssen mit dem aktuellen
Referenzlauf übereinstimmen. Damit können weder eine ähnlich benannte Baseline
noch Messwerte eines anderen Katalogausschnitts stillschweigend in das Gate
gelangen.

## 3) Ergebnis und nächster Schritt

Der Workflow bildet jetzt einen wiederverwendbaren Baseline-Kanal über mehrere
Läufe: Eine freigegebene Version wird explizit gewählt, gegen einen neuen
Kandidaten geprüft und nur auf Wunsch durch eine neue versionierte Promotion
ergänzt. Ein möglicher Folgepunkt ist eine Repository-Variable oder ein kleines
Manifest, das die aktuell empfohlene Run-ID und Artefaktversion als Alias hält,
ohne die explizite Provenienzprüfung aufzugeben.
