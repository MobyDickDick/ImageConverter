# AC0140_L: Nachprüfung des Plan-B-Nutzerexports

Der unverändert gesicherte Nutzerexport enthält einen gemeinsamen Versuch mit
17 Fällen, Seed `3810862661596591357` und 60 Sekunden Gesamtlimit pro Fall.
15 Ergebnisse bestehen die damalige Prüfung; `probe_05` und `probe_08` scheitern
mit `embedded_raster` und `no_vectors`. Ihr Bildvergleich ist nur deshalb exakt,
weil die Ausgabe das Originalraster einbettet. Es ist kein Vektorergebnis.

## Zwei nachgewiesene Ursachen

1. Der Fitter und die lokale Strukturprüfung setzten das Verlaufsrechteck mit der
   gesamten Zeichenfläche gleich. Die Plan-B-Varianten verschieben und skalieren
   das Motiv und fügen weisse Aussenränder hinzu. Bei beiden Fehlerfällen wurde
   die weisse Spalte bei x=2,5 fälschlich als Verlaufsmaximum gewählt. Das lag
   ausserhalb der zulässigen Startparameter: x=12,8–51,2 beziehungsweise
   x=13,6–54,4. Die Registrierung endete deshalb schon am Start. Bei weiteren
   grünen Fällen waren Rechteckränder und Verlauf ebenfalls an die Zeichenfläche
   statt an das sichtbare Motiv gebunden. Mehr Suchzeit hätte den unzulässigen
   Startwert nicht behoben; das reine Öffnen der Parametergrenzen hätte den
   weissen Aussenrand weiterhin mit dem Verlauf verwechselt.
2. Nach dem gescheiterten CLI-Versuch lag das Original unter
   `input/nonconvertable/`. Die nachgeschaltete native Wiederherstellung suchte
   nur unter `input/` und kehrte wegen der fehlenden Datei sofort zurück.
   Die OpenCV-Warnungen in beiden Exportprotokollen belegen diesen zweiten
   Fehler. Die Fälle endeten schon nach 3,516 beziehungsweise 3,578 Sekunden,
   obwohl 60 Sekunden Gesamtzeit vorhanden waren.

Die Erkennung bestimmt jetzt das zusammenhängende Rechteck im Raster und
vermisst Achsen, Raute, Verlauf und Linien innerhalb dieser Grenzen. Die
Koordinaten werden in die vollständige Zeichenfläche zurückgeführt; weisse
Ränder bleiben erhalten. Die Wiederherstellung löst die Quelldatei auch in den
beiden Archivordnern auf und lehnt mehrdeutige Quellen ab. Referenz-SVGs und
Fallnamen dienen weiterhin nicht als Rekonstruktionsvorlage.

## Nachweis

- [Alle 17 Fälle: Eingabe / korrigiertes SVG mit librsvg / Differenz](all-cases-comparison.png)
- [Korrigiertes Workbench-ZIP](corrected-plan-b-workbench.zip)
- [Kompakte Messdaten](summary.json)
- [Diagnose der alten Startparameter](diagnosis.json)
- [Frischer CLI-Lauf](replay.log) und [Einzelergebnisse](replay-results.json)
- [Prüfungen mit MuPDF und librsvg](renderer-checks.json)
- [113 bestandene Regressionen](tests-verified.log)

Alle **17/17** Fälle bestehen die unveränderten globalen Qualitätsgrenzen und
die Detailprüfung für Raute und hellen Innenstreifen. Die Hashes aller 17
Eingaberaster stimmen mit dem Nutzerexport überein. Quelle, Beschreibung,
Variantenparameter, Seed, 64 Iterationen und 60 Sekunden Gesamtlimit bleiben
gleich. Der Konverter hatte keinen Zugriff auf fremde SVG-Dateien.

Der neue Lauf dauerte zusammen 152,628 Sekunden; der längste Fall benötigte
25,046 Sekunden. Beide Renderer bestätigen alle 17 Ausgaben: **34/34** Prüfungen.
Der höchste normalisierte MSE ist 0,000379 mit MuPDF und 0,000685 mit librsvg;
die kleinsten Kantenwerte liegen bei 0,9015 und 0,8996. Die Übersicht wurde
zusätzlich visuell geprüft.

Eine separate Kopie ist in der laufenden GUI-Workbench verfügbar:
[korrigierte Aufgabe öffnen](http://127.0.0.1:8766/workbench?run=8f841329ef124ad3be658821f591a72a).
Die vorherige Aufgabe und das Nutzer-ZIP bleiben unverändert. Das neue ZIP
enthält den CLI-Lauf, alle Eingaben und Vektoren, Vergleichsbilder und die
zusätzlichen Renderer-Nachweise.

Die Regressionen prüfen zusätzlich zwei unabhängig konstruierte, deutlich
verschobene Motive mit weissen Aussenrändern, beschädigte Detailgegenproben,
die reale überwachte Wiederherstellung nach einer Quelldateiverschiebung sowie
mehrdeutige Archive. Die HTTP-/Prozessprüfungen wurden mit den benötigten lokalen
Socket- und Prozessrechten ausgeführt; der erste eingeschränkte Versuch war
durch `WinError 10013` blockiert. Die Grenzen wurden dafür nicht geändert.

Die Abnahme gilt für diesen Export und die genannten Gegenproben. Andere
Bildfamilien oder beliebig gedrehte beziehungsweise zusammengesetzte Szenen
sind damit nicht allgemein bestätigt.
