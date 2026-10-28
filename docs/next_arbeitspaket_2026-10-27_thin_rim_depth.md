# P0: Tiefenbelege bei dünnen, zwischen Pixelzentren liegenden Konturen

Teilumfang von **SEARCH-STRUCTURE-01**, Rang 1/P0 der
[verbindlichen Prioritätenliste](task_priority_2026-10-24.md).
Ausgangscommit `76087bcdb`; separater Branch
`codex/search-structure-thin-depth-evidence-2026-10-27`.
Die [vorherige Kreisrandarbeit](next_arbeitspaket_2026-10-25_owned_circle_rims.md)
dokumentiert genau diese offene Grenze und ihre Untersuchung als nächsten Schritt.

## Ursache und Umsetzung

Gleichfarbige überlappende Instanzen benötigen sichtbare Konturen als
Tiefenbeleg. `_rim_front` prüft bisher einen um Antialiasing bereinigten
Konturstreifen an Pixelzentren. Ein schmaler achsenparalleler Streifen kann
auf seiner gesamten Länge zwischen diesen Zentren liegen. Die fünf
erforderlichen Beobachtungen fehlen dann trotz sichtbarer Kontur.

Die bisherige Prüfung bleibt der erste Weg. Nur bei weniger als fünf
geometrisch geeigneten Pixelzentren entsteht eine zusätzliche Abtastung:
Ein festes 8×8-Flächenraster pro vorhandenem Bildpixel schätzt dessen Anteil
an der nativen Kontur. Mindestens die Hälfte des Pixels muss im Rand liegen;
alle 64 Teilpunkte müssen innerhalb der anderen Füllung und außerhalb der
erweiterten Silhouetten sämtlicher Drittobjekte liegen.

Die Teilpunkte schätzen ausschließlich die Geometrie. Es werden keine
Bildwerte interpoliert und keine zusätzlichen Rasterbeobachtungen erfunden.
Mindestens fünf **verschiedene Originalpixel** sind weiterhin erforderlich.
Gemessen werden ihre vorhandenen Farben mit denselben Kontrast-,
Farbgeraden-, Deckungs- und Unterstützungsgrenzen wie bisher. Ein Rand muss
sichtbar sein, der andere überdeckt. Die Reihenfolge wird auch während der
Registrierung erneut geprüft. Objekt-, Relations-, lokale und globale
Rastergates, Bildbudget und Strukturzustandsgrenze bleiben erhalten.

Der Code verwendet weder Bildnamen noch Sollgeometrien, Referenz-SVGs oder
neue Symbolvorlagen. Die alternative Abtastung ist auf die kleine
Paarüberdeckungsregion begrenzt und hat eine feste Anzahl Teilpunkte.

## Vorher/Nachher und Grenzen

Die zwölf synthetischen Kreis-/Rechteckszenen mit Seed `529713`, zwei
Kindern, eckigen Rechtecken, gleichen Füllfarben und hellen Konturen wurden
vor der Runtime-Änderung erzeugt. Ein vollständig mit dem ursprünglichen
Produktionsmodul wiederholter CLI-Lauf besteht **11/12**, die geänderte
Runtime besteht auf denselben Rasterbytes **12/12**. Der bisher konservativ
abgelehnte Fall 06 besteht nun auch die unabhängige native Objekt-, Regions-
und vollständige Pixelprüfung. Fünf Sekunden pro Bild und alle Gates sind
unverändert.

Die Gegenproben prüfen beide Zeichenreihenfolgen, drei Subpixelpositionen,
fehlende Konturen, widersprüchlich sichtbare Ränder, Drittobjekte, nur vier
verfügbare Bildpixel, zu geringe geometrische Randdeckung und Fremdfarben.
Der bisherige Sonderfall im Kreisrandtest verlangt jetzt die vollständige
positive Abnahme statt einer absichtlichen Ablehnung.

Der finale betroffene Regressionsblock besteht **215/215**, das Kernprofil
**42/42**, jeweils Exit 0. Ein zusätzlicher Seed `853197` besteht **12/12**,
die gekoppelte Prüfung mit Seed `529713` und 16 Varianten **17/17**, jeweils
über die echte CLI. Ein zuvor unterbrochener Regressionsträger ohne
Endergebnis zählt nicht als Abnahme; der vollständige finale Block wurde
anschließend separat ausgeführt. Lokales Python: 3.10.11.

Reproduktion der primären Kohorte:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --prepare .tmp/thin-depth-inputs --seed 529713 --children 2 --outlines --same-fill
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --inputs .tmp/thin-depth-inputs --output .tmp/thin-depth-after --require-all
```

Die Verzeichnisse dürfen beim Start noch nicht existieren. Für den
Vorhervergleich denselben Generator und dieselben gesicherten Eingaben mit
dem unveränderten Produktionsmodul aus `76087bcdb` verwenden. Jeder CLI-Bericht
sichert die Runtime- und Eingabehashes. Kompakte Ergebnisse und weitere
Prüfbefehle stehen unter
[`thin_rim_depth_v1`](../artifacts/evaluation/thin_rim_depth_v1/README.md).
Generierte Raster, Vektoren und vollständige Logs bleiben unter `.tmp/`.

Dies ist ein synthetischer Teilabschluss des höchsten Arbeitspakets.
Allgemeine Komposition und unabhängige reale Familienabnahme bleiben offen;
**SEARCH-STRUCTURE-01 wird insgesamt nicht geschlossen**. Es wird weder eine
höhere Katalogerfolgszahl noch eine grüne vollständige Standardsuite behauptet.

## Einordnung von Keras

Keras ist eine mögliche Grundlage für bessere Vorschläge: Die offiziellen
[Computer-Vision-Beispiele](https://keras.io/examples/vision/) enthalten
Objektdetektion, Segmentierung und Kontursegmentierung. Für dieses Projekt
wären insbesondere getrennte Instanzmasken und sichtbare Randabschnitte
hilfreich. Daraus könnten alternative native Formen und Schichten entstehen;
die bestehenden semantischen und Rasterprüfungen müssten sie weiter abnehmen.

Der [bisherige reale Netzversuch](history/next_arbeitspaket_2026-10-19_neural_real_regions.md)
liefert jedoch keinen belastbaren Konvertierungsgewinn: analytisch 71/90,
mit optionalem CNN 72/90 vollständige Freigaben, 88/90 bytegleiche SVG-Paare,
keine zusätzlichen Szenenkandidaten in 89 beobachteten Netzaufrufen. Diese
90 Versuche beruhen auf zehn realen Familien und mehreren Seeds, nicht auf
90 unabhängigen Familien. Das Ergebnis widerlegt weder Keras noch ein
anderes Modell; es zeigt den fehlenden Nutzen des damaligen Anschlusses.

Ein sinnvoller späterer Versuch benötigt unabhängig markierte Instanz-/Randdaten,
eine Trennung nach Quellfamilien vor jeder Augmentation und einen Vergleich
der fertigen SVGs bei gleichem Gesamtbudget. Ein Frameworkwechsel allein
behebt die nachgewiesene Kompositionslücke nicht. Entsprechend der Rangliste
bleibt ein solcher Netzversuch P2; dieses P0-Paket führt keine neue
Frameworkabhängigkeit ein.

## Sitzungslog

- Getestet: gepaarte CLI-Kohorte, Zusatzseed, Varianten, Negativkontrollen und betroffene Regression.
- Ergebnis: 11/12 → 12/12; zusätzlich 12/12 und 17/17, Regression 215/215, Kernprofil 42/42.
- Blocker: allgemeine Komposition und unabhängige reale Familienabnahme bleiben offen.
- Nächster Schritt: reale Familien vor weiterer Entwicklung sperren und den gemeinsamen Szenenvertrag prüfen.
- Startbefehl: `.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 529713 --children 2 --outlines --same-fill`.
