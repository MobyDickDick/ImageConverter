# Plan-B: Röhrenvarianten AC0151_L

Das übergebene `plan-b-workbench(1).zip` enthält einen abgeschlossenen Lauf mit
Seed `6710666133029594656`, 64 Iterationen und 60 Sekunden je Fall. Das Original
besteht; alle 16 Varianten scheitern an MSE und Kantenübereinstimmung. Technische
Fehler enthält der übergebene Lauf nicht.

## Ursachen und Korrektur

Zwei Hypothesen wurden getrennt an den unveränderten Rasterbildern geprüft:

1. **Beschreibung:** `tube_contract` akzeptiert nur die vollständige kurze oder
   ausführliche Grundbeschreibung. Der globale Satz der Workbench zu Größe und
   Lage verhindert bei allen Varianten bereits die Auswahl des Röhrenmodells.
   Stattdessen entstehen im allgemeinen Fallback flache Verläufe und Linien.
2. **Rastergeometrie:** Auch mit überbrückter Beschreibungsprüfung verwirft der
   alte Röhrenfitter sämtliche 16 Raster. Bei verschobenen oder skalierten
   Rechtecken liegen die Kanten zwischen Pixeln. Übereinander gerenderte
   Farbflächen erzeugen dort chromatische Mischpixel, auch am äußeren Rand
   einer grauen Kappe. Diese werden als Anfang des farbigen Körpers oder als
   unzulässige Kappenfarbe fehlgedeutet. Ganzzahlige Außenkanten verfehlen
   außerdem die unveränderten Kanten- und lokalen Kappenprüfungen.

Die Textprüfung konsumiert jetzt genau einen vollständigen abschließenden
Workbench-Satz. Zusätzliche Objekte, Negationen, Text vor oder nach diesem Satz
und doppelte Sätze werden weiterhin abgewiesen. Die Geometrie stammt aus dem
Raster, nicht aus dem Beschreibungssatz.

Die Körpererkennung verwendet den längsten zusammenhängenden chromatischen
Zeilenabschnitt. Kappenfarben werden aus inneren Spalten bestimmt; die
Auswertung bleibt auf denselben Bildkoordinaten. Die vier Außenkanten und zwei
Kappenübergänge werden anschließend mit tatsächlich gerenderten Kandidaten
verfeinert: höchstens zwei Koordinatendurchläufe je Schrittweite von 0,5 bis
0,0625 Pixel, höchstens 1,5 Pixel Abstand vom Startwert. Der erste Durchlauf
prüft mehrere Positionen innerhalb eines Randpixels, da der Fehler bei mehreren
übereinanderliegenden Flächen nicht monoton sein muss. Bereits geprüfte
Kandidaten werden nicht erneut gerendert; das aktive Zeitlimit gilt auch hier.

Pixelgrenzen, lokale Kappen-/Körperprüfung und Modellstruktur bleiben erhalten:
vier native Rechtecke mit insgesamt 14 Verlaufsstopps, keine Rastereinbettung,
keine nachgezeichneten Pfade, kein Zugriff auf Referenz-SVGs im Konverter.

## Nachweis

Das Paket bleibt unter
`artifacts/evaluation/gradient_tube_plan_b_2026-11-14/replay` erhalten.
`attempt_0001` ist der ursprüngliche Fehllauf. Im ersten Korrekturlauf bestehen
15 Fälle; zwei Prozesse melden nach einer Unterbrechung der Ausführungsumgebung
Zeitüberschreitungen. Diese technischen Fehler bleiben als `attempt_0002`
sichtbar. Der abschließende gemeinsame `attempt_0003` besteht alle 17 Fälle.

```powershell
.venv/Scripts/python.exe -m tools.plan_b_workbench --run-dir artifacts/evaluation/gradient_tube_plan_b_2026-11-14/replay --cases all --iterations 64 --timeout-seconds 60
```

Alle Eingabehashes, vollständigen Beschreibungen, Seed und Budgets entsprechen
dem ursprünglichen Lauf. Jede Ausgabe ist erneut das native Röhrenmodell;
sämtliche lokalen Detailprüfungen bestehen. Die Referenzzugriffsaudits enthalten
keine verbotenen SVG-Zugriffe. Die kleinste Kantenübereinstimmung beträgt
0,79893 bei geforderten 0,72; die kleinste Vordergrundüberdeckung 0,99056 bei
geforderten 0,85. Die höchste normierte MSE beträgt 0,00001467 bei erlaubten
0,01. Die Summe der Falllaufzeiten beträgt 97,624 Sekunden; parallele
Regressionstests beeinflussen diese Laufzeit, sie ist kein isolierter Benchmark.

139 gezielte Tests bestehen:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_gradient_tube_runtime.py tests/detailtests/test_iteration_initialization_helpers.py tests/detailtests/test_rendering_gradient_compatibility.py tests/test_axial_panel_runtime.py tests/detailtests/test_plan_b_workbench.py
```

Die neuen Prüfungen umfassen 16 unabhängig erzeugte Röhrenvarianten mit anderen
Farben, Stopp-Positionen, Proportionen und Seed, beide Beschreibungsfassungen,
unerlaubte Zusätze und Budgetablauf während der Kantensuche. Die bestehenden
Gegenproben für verlorene Kappen, falsche Farben, zusätzliche Bildobjekte,
entfernte Verläufe und die drei JPEG-Größen bestehen ebenfalls. Die HTTP-Tests
benötigen lokale Socketrechte; der erste eingeschränkte Testlauf scheiterte
daran, der abschließende Lauf mit diesen Rechten besteht vollständig.

`summary.json` enthält Einzelmesswerte, Hashes, Modellprüfungen, Renderzahlen
und Softwarefingerabdrücke. `comparison.png` zeigt eine Variante vor und nach
der Korrektur. `plan-b-workbench-corrected.zip` enthält alle drei Versuche und
die aktualisierte CSV. Die bereits vorhandene lokale GUI-Aufgabe
`71b65e2a8f1941a192f10e139fa7ca36` besteht ebenfalls alle 17 Fälle in einem
neuen gemeinsamen Versuch mit denselben Eingaben; ihr erster Versuch bleibt
erhalten. Die aktualisierten Ergebnisse erscheinen beim Neuladen der Aufgabe.
16 Ausgaben sind bytegleich zum Wiederholungslauf. Bei `probe_15` liefert die
zusätzliche generische Feinoptimierung einen leicht anderen Verlaufsstopp;
beide Ausgaben bestehen die Modell-, Detail- und Pixelprüfungen. Der gleiche
Seed bedeutet bei dieser zeitbegrenzten Nachoptimierung keine garantierte
Bytegleichheit.

Die Abnahme gilt für die untersuchte Aufgabe und die genannten Gegenproben,
nicht für beliebige Röhrenformen, Farben oder Anbauten.
