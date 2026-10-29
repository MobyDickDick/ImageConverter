# AC0835 und echte Suchalternativen, 29. Oktober 2026

AC0835 wurde mit der unveränderten Katalogbeschreibung in einen älteren
Kreis-/Textzeichenpfad gelenkt. Die zusätzliche Portfoliosuche prüfte dort
**0 Kandidaten**. Der erneute alte CLI-Versuch änderte den schlechten Entwurf
nicht. Die Anforderung wörtlicher Schlüsselwörter wie `Kreisscheibe`, `einfarbig`,
`serifenlos` und `keine Anschlüsse` verhinderte die passende Kurztextregistrierung.
Bei L kam eine unnötige Ablehnung hinzu: 19 beobachtete Pixel Schriftbreite
überschritten die 18,9756-Pixel-Zulassung knapp.

Die Korrektur gilt für beschriebene kurze Kreislabels allgemein. Explizit
verneinte Griffe werden als Abwesenheit erkannt; Rasterbelege bestimmen Kreis,
Farben und Schrift. Die Zulassung berücksichtigt die Pixelrundung, und das
gemeinsame native Textmodell passt die horizontale Schriftbreite unabhängig
von der Höhe an (begrenzt auf 60–140 %). Einzeln positionierte Zeichen und deren
zusätzliche Schriftkontur bleiben als konkurrierende Modelle erhalten.
Es wurden keine Bildnamen oder gespeicherten SVGs in den Laufzeitpfad eingebaut.

## Abnahme

Zwei frische reguläre `semantic-only`-CLI-Läufe mit Seeds 42 und 314159 verarbeiten
dieselben drei JPEGs unter neutralen Namen `PROBE_L/M/S`. Sie benutzen die
ursprüngliche Beschreibung; die Worker melden keine verbotenen SVG-Lesezugriffe.
Alle sechs Ausgaben bestehen sowohl MuPDF als auch die unabhängige librsvg-Prüfung.
Label und native Primitive werden zusätzlich geprüft. Die unveränderten Grenzen
sind MSE ≤ 0,01, Vordergrund-MSE ≤ 0,04, Kantendeckung ≥ 0,72 und Vordergrund-IoU ≥ 0,85.

| Grösse | MSE intern | MSE librsvg | IoU librsvg | Kantendeckung librsvg |
|---|---:|---:|---:|---:|
| L | 0,00272 | 0,00259 | 0,8614 | 0,9125 |
| M | 0,00275 | 0,00252 | 0,8610 | 0,9188 |
| S | 0,00290 | 0,00292 | 0,9106 | 0,8923 |

Die beiden Seeds liefern pro Grösse byteidentische bestandene SVGs, obwohl sich
die Reihenfolge und teilweise die Anzahl der Kandidaten unterscheiden: L 831/831,
M 369/306, S 242/350. Gleiche Ergebnisse beweisen keine Scheinsuche. Auch eine
erfolglose echte Suche darf denselben besten Entwurf behalten. Zufällige sichtbare
Änderungen allein wären kein Qualitätsnachweis.

Die drei SVGs sind in `artifacts/converted_images/converted_svgs`, im
Zufriedenstellend-Archiv und in der dazugehörigen Regression aktualisiert.
Historische Legacy-Baselines bleiben als Vergleich erhalten. `manifest.json`
und `summary.json` pinnen Original- und SVG-Hashes sowie die neue Abnahme;
der Archivindex verweist auf diese Evidenz. Der Archivumfang bleibt 379 Paare.

## Wiederholen

```powershell
.venv/Scripts/python.exe -m tools.recheck_short_label_family --family AC0835 --output-dir .tmp/ac0835-recheck --seed 42 --seed 314159
```

Das Ziel muss neu sein. Der Befehl erzeugt frische Konvertierungen und prüft
gespeicherte Vektoren mit beiden Renderern sowie auf das beschriebene Label.
Rohprotokolle und der visuelle Vergleich liegen lokal in diesem Evidenzordner.

Die GUI vergibt jetzt ausdrücklich einen frischen, gespeicherten Seed je Start.
Bei einem Entwurf zeigt sie die tatsächliche Kandidatenzahl, einen nicht
angeschlossenen Suchweg und gegebenenfalls denselben Wiederholungsentwurf an.
Das ist eine Diagnose der aktuellen Modellgrenzen, keine allgemeine Behauptung,
dass der Konverter beliebige Motive bereits rekonstruieren kann.
