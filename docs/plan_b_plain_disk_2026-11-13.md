# Plan-B: Varianten eines kleinen grauen Kreises

Das übergebene `plan-b-workbench.zip` enthält einen echten Fehllauf mit Seed
`8019332433889847450`, 64 Iterationen und 60 Sekunden Zeitlimit je Fall.
Das Original besteht. Alle 13 abgeschlossenen Varianten scheitern an der
Vordergrundüberdeckung, zehn zusätzlich an der Kantenausrichtung. Vor der
14. Variante bricht der Lauf beim Ersetzen von `report.json` mit
`PermissionError: [WinError 5]` ab. Drei Varianten wurden nicht ausgeführt.

## Ursachenprüfung

Zwei Hypothesen wurden an den gesicherten Eingaben unterschieden:

1. Die erweiterte Zeichenfläche oder die Subpixelverschiebung verhindert den
   Kreisfit. Gegenprobe: Die unveränderten 17 Raster mit der ursprünglichen
   Beschreibung direkt an `fit_plain_disk` übergeben. Alle bestehen die
   unveränderten unabhängigen Qualitätsgrenzen. Die Rastergeometrie allein
   erklärt den Fehler damit nicht.
2. Der ergänzte relative Beschreibungssatz verhindert die Modellauswahl.
   Bestätigt: Die vollständige Beschreibung der ersten Variante wird bereits
   vor der Rasterprüfung vom bisherigen vollständigen Regex-Match abgewiesen.
   Im archivierten CLI-Protokoll fehlt die Kreisregistrierung; stattdessen
   erzeugt die allgemeine Suche Rechtecke und zusätzliche Linien.

Die Beschreibungsprüfung erlaubt jetzt zusätzlich den globalen Satz zu
Skalierung und Verschiebung, den die Varianten erzeugen. Sie bleibt vollständig
verankert: Zusätzlicher Text, Punkte oder Rechtecke vor oder nach diesem Satz
werden weiterhin abgewiesen. Mittelpunkt, Radius, Strichbreite und Farben
werden weiterhin aus dem Raster gefittet. Lokale Prüfungen gegen verlorene
Bilddetails und sämtliche Qualitätsgrenzen bleiben bestehen.

Der Speicherfehler ist davon unabhängig. Windows kann das atomare Ersetzen
einer noch geöffneten Datei verweigern; welcher Leser die Datei im Fehllauf
geöffnet hielt, ist nicht protokolliert. `save_report` schreibt einen eigenen
temporären Dateinamen und wiederholt das Ersetzen bei `PermissionError` bis zu
achtmal mit insgesamt höchstens 1,27 Sekunden Wartezeit. Die vorherige JSON-Datei
bleibt vollständig lesbar. Bei dauerhaftem Fehler wird weiterhin eine Ausnahme
gemeldet; die ungesicherte neue Fassung bleibt als `report.<Kennung>.tmp` erhalten.

## Nachweis

Das Originalpaket wurde nach
`artifacts/evaluation/plain_disk_plan_b_2026-11-13/replay` kopiert.
Der alte Versuch bleibt unverändert erhalten. Der zweite Versuch verwendet
dieselben 17 Rasterhashes, vollständigen Beschreibungen, Seed und Budgets:

```powershell
.venv/Scripts/python.exe -m tools.plan_b_workbench --run-dir artifacts/evaluation/plain_disk_plan_b_2026-11-13/replay --cases all --iterations 64 --timeout-seconds 60
```

Alle 17 Fälle bestehen über die echte `semantic-only`-CLI. Jeder Fall erzeugt
genau ein Hintergrundrechteck und einen nativen Kreis; alle Prozesse enden mit
Exitcode 0. Der Audit-Hook protokolliert keine fremden SVG-Zugriffe. Die kleinste
Vordergrundüberdeckung beträgt 0,97087 bei geforderten 0,85, die kleinste
Kantenausrichtung 0,94375 bei geforderten 0,72. Die Summe der Falllaufzeiten
beträgt 46,028 Sekunden; die Kreisregistrierungen melden 4585 Renderprüfungen.
Dies ist ein Nachweis für diese Aufgabe, kein allgemeiner Erfolg für alle Motive.

Regressionen prüfen zusätzlich 16 Varianten einer unabhängigen farbigen,
versetzten Kreisvorlage mit neuem Seed, die drei Kataloggrößen, unzulässige
Zusatzinhalte, kleine ungenannte Bilddetails sowie vorübergehende und dauerhafte
Dateisperren. Die Tests übergeben dem Fitter ausschließlich Raster und Text.

Kompakte Messdaten und Quellhashes stehen in
`artifacts/evaluation/plain_disk_plan_b_2026-11-13/summary.json`.
Der lokale Vergleich `comparison.png` und das Paket
`plan-b-workbench-corrected.zip` enthalten die alten und neuen Ergebnisse.
