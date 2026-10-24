# Plan B: GitHub und lokale Nachweise kontrolliert vergleichen

Der [GitHub-Lauf 40097155375](https://github.com/MobyDickDick/ImageConverter/actions/runs/40097155375)
auf `854be74c2` beendet den Abnahmeschritt nach rund 25 Sekunden mit Exit 1.
Installation, Berichtserstellung und Artefakt-Upload bestehen. Alle neun
zufällig ausgewählten Originale verfehlen Qualitäts- oder Vektorkriterien;
ihre 16 Varianten starten deshalb nicht. Dies ist in diesem Lauf kein Timeout.

Die bisherigen lokalen 17/17-Nachweise verwenden gezielt erzeugte synthetische
Entwicklungsszenen. Sie sind keine Abnahme des zufälligen Katalogbestands.
Ein neuer Seed oder das Weiterprobieren nach Originalfehlern repariert die
Konvertierung nicht; ältere Fehler bleiben Aufgaben.

## Exakte lokale Wiederholung

Das erste Original, [Issue #2025](https://github.com/MobyDickDick/ImageConverter/issues/2025),
wurde mit identischem SVG-Hash, Beschreibungshash, Beschreibung, Seed
`209704809607928206`, 64 Iterationen und 60 Sekunden Prozess-Timeout lokal
über den echten Plan-B-Runner wiederholt. Es scheitert auch lokal.

| Messung | GitHub und lokal identisch |
| --- | ---: |
| RGB-MSE | 0.012214812450110912 |
| Vordergrund-MSE | 0.07406366616487503 |
| Kontur | 0.8447351455688477 |
| IoU | 0.6451612903225806 |

Die drei Fehlercodes sind ebenfalls gleich. Die Bildbibliotheken sind auf
beiden Seiten NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7 und Pillow 12.3.0.
Python ist lokal 3.10.11/Windows, im untersuchten CI-Lauf 3.10.22/Linux.
Für diesen Fall erklärt die Plattform den Fehlschlag somit nicht. Daraus
folgt keine Plattformgleichheit für alle Bilder.

Die kompakte Gegenprobe steht in
[`summary.json`](../artifacts/evaluation/plan_b_ci_diagnostics_v1/summary.json).
Vollständige lokale Debug-Daten liegen unter `.tmp/plan-b-ci-replay/`:
Quelle, Beschreibung, Originalraster, Ausgabe-SVG, Vergleich/Differenz und Log.

## Diagnose für kommende GitHub-Läufe

Der Workflow verwendet jetzt `--keep-debug-artifacts` und ungepufferte Python-
Ausgabe. `plan-b-acceptance` enthält Quelle, Beschreibung, Variantenreferenzen,
Raster, Konvertierungen, vollständige CLI-Logs, Such-/Laufdiagnosen sowie
Vergleichs- und Differenzbilder, soweit der Prozess sie erzeugen konnte.
Bei Vorbereitungsfehlern bleiben die bis dahin erzeugten Daten erhalten.
`plan-b-diagnostics` ergänzt Commit-ID, Python-/Paketversionen und Plattform.
Beide Artefakte bleiben 14 Tage erhalten. Der Nutzer hat dies ausdrücklich
freigegeben. Das Abnahmeartefakt behält seine bisherige Verzeichnisstruktur,
damit der Folgeworkflow die Fehleraufgaben weiterhin findet.

Manuelle Läufe können optional den protokollierten Auswahlseed verwenden.
Eine exakte Wiederholung erfordert auch denselben Commit, Eingabebestand
und dieselbe Toolchain. Ein Original lässt sich isoliert wiederholen:

```powershell
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/samples/AC0050_L.svg --description-file .tmp/plan-b-ci-replay/source_description.txt --seed 209704809607928206 --iterations 64 --timeout-seconds 60 --keep-debug-artifacts
```

Qualitätsgrenzen, Zufallsauswahl und rote Abnahme bei ungenügender Qualität
bleiben verbindlich. Identische gerasterte Varianten bei sehr kleinen
Vorlagen, etwa Issue #1980, bleiben als eigener technischer Fehler offen.
