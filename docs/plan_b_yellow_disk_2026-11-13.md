# Plan-B: gelber Verlaufskreis GE0281

Das übergebene `plan-b-workbench.zip` enthält einen vollständig abgeschlossenen
Lauf mit Seed `4091935898698028088`, 64 Iterationen und 60 Sekunden je Fall.
14 von 17 Fällen bestehen. `probe_03`, `probe_09` und `probe_15` unterschreiten
die unveränderte Kantenübereinstimmung von 0,72 (0,60091 / 0,68252 / 0,69103).
Es gibt keine technischen Ausführungsfehler.

## Ursache und Gegenprobe

Die Beschreibung der neun Varianten 03, 06, 09, 10, 11, 13, 14, 15 und 16 enthält
das Wort **geringfügig**. Die Radialkreiserkennung schloss Beschreibungen mit
der Teilzeichenfolge `ring` aus. Damit deutete sie auch `ge[ring]fügig` als
Ringbeschreibung und brach bereits vor der Rasterprüfung ab.

Der allgemeine Suchweg erzeugte anschließend einen flachen Kreis mit zusätzlichen
Linien statt eines einzelnen Kreises mit radialem Farbverlauf. Sechs dieser neun
semantisch unpassenden Ergebnisse bestanden trotzdem die generischen Pixelgates.
Die 14 bestandenen Fälle des alten Laufs bedeuten daher keine vollständige
inhaltliche Abnahme.

Zwei Hypothesen wurden getrennt geprüft: Fehler durch die erweiterte Rasterfläche
beziehungsweise Subpixelverschiebung, und Fehler durch den Beschreibungstext.
Mit der ursprünglichen Beschreibung bestehen dieselben 17 Rasterbilder bereits
mit dem alten Fitter sämtliche unveränderten Qualitätsgrenzen. Der Trace zeigt
bei allen neun betroffenen vollständigen Beschreibungen den vorzeitigen Abbruch
an der Ringprüfung. Die Rastergeometrie erklärt diese Ausfälle somit nicht.

Die Ringprüfung verlangt jetzt eine Wortgrenze vor `Ring` beziehungsweise
`Kreisring`; `Ringförmig` bleibt ebenfalls ausgeschlossen. Das Wort `geringfügig`
verhindert die Auswahl des Radialkreismodells nicht mehr. Rasterprüfung,
Parametersuche und Qualitätsgrenzen bleiben unverändert.

## Nachweis

Das Originalpaket wurde in einen eigenen lokalen Wiederholungsordner kopiert.
`attempt_0001` bleibt erhalten. Der zweite Versuch verwendet identische
Rasterhashes, vollständige Beschreibungen, Seed und Budgets:

```powershell
.venv/Scripts/python.exe -m tools.plan_b_workbench --run-dir artifacts/evaluation/yellow_disk_plan_b_2026-11-13/replay --cases all --iterations 64 --timeout-seconds 60
```

Alle 17 Fälle bestehen über die echte `semantic-only`-CLI mit Exitcode 0.
Jede Ausgabe enthält genau ein Hintergrundrechteck und einen Kreis mit radialem
Farbverlauf. Es gibt keine protokollierten fremden SVG-Zugriffe.
Die kleinste Kantenübereinstimmung beträgt 0,91022, die kleinste
Vordergrundüberdeckung 0,97027. Die Summe der Falllaufzeiten beträgt vorher
333,561 und nachher 63,972 Sekunden; dies ist kein isolierter Laufzeitbenchmark.

40 Radialkreistests und 22 Workbench-Tests bestehen. Die neuen Tests reproduzieren
den Fehler vor der Korrektur, erhalten echte Ring-Ausschlüsse und vergleichen
16 unabhängige Farb-/Lagevarianten mit und ohne den ergänzten Beschreibungssatz
auf bytegleiche Ausgabe. Diese Textinvarianz erweitert nicht die bestehenden
Qualitätsgrenzen des Fitters: Eine dieser unabhängigen Varianten verfehlt bereits
mit der Basisbeschreibung ein Pixelgate. Der vollständige 17-Fälle-Pass gilt
für die hier untersuchte gelbe Aufgabe.

Messwerte, Hashes und Softwarefingerabdruck stehen in
`artifacts/evaluation/yellow_disk_plan_b_2026-11-13/summary.json`.
Das lokale `plan-b-workbench-corrected.zip` im selben Ordner enthält beide
Versuche und die aktualisierte CSV. Bereits geöffnete Aufgaben behalten ihre
alten Messwerte, bis ein neuer Versuch ausgeführt wird.
