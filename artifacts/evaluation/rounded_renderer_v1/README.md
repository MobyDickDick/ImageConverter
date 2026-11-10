# Native Rundungen: unabhängiger Renderer- und CLI-Nachweis

Paket **SVG-ROUNDED-RENDERER-01**, Ausgangscommit `409b451f7`.
[Umsetzung, Reproduktion und Grenzen](../../../docs/next_arbeitspaket_2026-11-06_rounded_renderer.md).
Status: **Review**, synthetischer Abschluss mit dokumentiertem
zeitabhängigen Bestandsnachlauf. Der endgültige Prüfstand steht in `checks.json`.

| Kohorte | Referenz | Ergebnis |
| --- | --- | ---: |
| 28 gesicherte Renderkontrollen, global vorher/nachher | unveränderte librsvg-PNGs | 23/28 → 28/28 |
| 96 lokale Kontrollecken vorher/nachher | dieselben PNGs | 40/96 → 96/96 |
| Primäre echte CLI, Seed 624873, vorher/nachher | vor Runtimeänderung mit librsvg gesichert | 2/12 → 12/12 |
| Zusätzliche echte CLI, Seed 981347 | eigene librsvg-Kohorte | 12/12 |
| Eine gekoppelte Variantenkohorte, Seed 853291 | eigene librsvg-Kohorte | 17/17 |

Alle 41 neuen CLI-Vektoren bestehen native Objekt-, Radius-, Kontur-,
Verlaufs-, Eltern- und Tiefenprüfungen sowie globale und objektlokale
Rastergates. Beide Renderer bestehen außerdem je 164/164 Elternecken.
Der größte native Radiusfehler beträgt 0,2575 Pixel; das unabhängige Gate
bleibt 1,25 Pixel. Die endgültige überwachte Prozesszeit bleibt lokal unter
fünf Sekunden (höchstens 4,672 Sekunden); keine allgemeine Laufzeitgarantie.
Bildbudget fünf Sekunden, acht Kinder und 96 Strukturzustände bleiben bestehen.

Die gemeinsame Regression besteht 1.206/1.207 Prüfungen, Exit 1, ohne
Überspringung, in 651,57 Sekunden unter einem 2.400-Sekunden-Guard. Der eine
Acht-Objekte-Bestandsfall liefert nach 5,149 Sekunden kein Ergebnis bei fünf
Sekunden Bildbudget. Er besteht isoliert (1/1) und im kompletten Modulnachlauf
(32/32, Exit 0). Die JUnit-Knoten sind gegengeprüft; ursprünglicher Fehler und
Nachlauf bleiben getrennt erhalten. Kernprofil 42/42, gezielte
Beobachtungsprüfung 140/140, jeweils Exit 0 ohne Überspringung. Keine Grenze
wird erhöht. Die Laufzeitabweichung des langen Laufs bleibt eine ausdrückliche
Abnahmegrenze; es gibt keinen pauschalen grünen Standardsuite-Nachweis.

Der analytische Eckverlust für Radius 30 beträgt 193,1417 Quadratpixel.
MuPDF verbessert sich von 234,9529 auf 192,6824; librsvg misst 193,8471.
Füllung, Verlauf und Kontur verwenden denselben korrigierten privaten Pfad.
Gespeicherte SVGs behalten native Rechtecke und richtige Radien. Diagonale
Objektboxverläufe und die belegte Konturfarbmessung sind gemeinsam korrigiert.

Die historischen MuPDF-Eingaben, Markierungen und Ausgaben bleiben bytegenau
erhalten. Ihr ursprünglicher Prüfstand (41/41 MuPDF, aber nur 121/164
librsvg-Ecken) wird nicht als neue Abnahme verwendet. Eine erneute CLI auf
denselben alten Rastern besteht zwar die Pixelgates, braucht aber falsche
native Elternradien; die unabhängige Objektprüfung nimmt deshalb 0/41 ab.
Diese Negativmenge bleibt ausdrücklich außerhalb der neuen Erfolgskohorte.

`summary.json` enthält getrennte Kontroll-, neue CLI-, historische Ausgabe-
und historische Wiederholungskohorten. Es sichert Eingabe-, Beschreibungs-,
Annotations-, Referenz-, Ausgabe-, Berichts- und Runtimehashes, alle vier
Elternecken, Objektgates und Radiusfehler. `checks.json` enthält Befehle,
Exitcodes, Zeitlimits und Testberichtshashes, einschließlich negativer
Entwicklungsproben. Exit 0 eines historischen Laufs ohne `--require-all`
besagt lediglich, dass alle Fälle vollständig protokolliert wurden.

Die unabhängigen Kontroll-SVGs und PNGs liegen in
[`tests/fixtures/rounded_renderer`](../../../tests/fixtures/rounded_renderer/README.md).
Ein zusätzliches historisches gleichfarbiges Raster bleibt per Prüfsumme
gesichert. Null oder eine freie Ecke bleiben negative Beobachtungen; zwei
bis vier freie Ecken müssen den gemessenen Radius tragen.

Rohdaten und Logs liegen lokal unter `.tmp/rounded-renderer/`. Die Werkzeuge
erzeugen frische Referenz- und CLI-Bäume; CI prüft die eingefrorenen Kontrollen
und einen zusätzlichen unabhängigen librsvg-Szenenseed mit der echten CLI.
Nur synthetische Abnahme: HC0010 und Rail bleiben `sealed_unrun`, Katalog und
Konvertierungsarchiv unverändert, die übergeordneten P0-/Realabnahmen offen.
Als nächstes folgt
[SEARCH-STRUCTURE-CLIPPED-RECTANGULAR-PARENT](../../../docs/next_arbeitspaket_2026-11-07_clipped_rectangular_parent.md).
