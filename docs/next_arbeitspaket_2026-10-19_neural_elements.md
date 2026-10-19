# NEURAL-ELEMENTS-01 – optionaler CNN-Versuch mit negativem Ergebnis

Stand: 19. Oktober 2026. Das nächste dokumentierte Architekturpaket nach
COMPONENT-VALUE-01 wurde als begrenzter Erkennungsversuch durchgeführt.
**Kein nachgewiesener End-to-End-Nutzen: Der analytische Standard bleibt aktiv.**
Die produktive Netzabnahme ist damit nicht erreicht. Ein brauchbarer
Forschungsversuch darf auch ein negatives Ergebnis haben; das Netz wird weder
automatisch aktiviert noch zur Entfernung bestehender Erkenner verwendet.

## Umsetzung

`imageCompositeConverterNeuralElements.py` implementiert ein kleines tatsächlich
trainiertes Faltungsnetz mit sechs Klassen: Kreis, Rechteck, Dreieck, Linie,
Textbereich und unbekannt. Die Architektur verwendet 16×16 Pixel, sechs lernbare
3×3-Faltungen, ReLU, 2×2-Mittelwertpooling und einen Softmax-Ausgang. Training
und Inferenz benötigen ausschließlich die vorhandenen NumPy-/OpenCV-Pakete.
Das JSON-Modell enthält 1.830 Parameter; es lädt keine Trainingsbilder oder
Referenz-SVGs. Der Versuch enthält kein vortrainiertes Fremdmodell. Eine solche
Variante samt zusätzlichem Framework wurde für diesen ersten Umfang nicht
untersucht und bleibt eine ausdrücklich ungemessene Alternative.

`--neural-elements-model <JSON>` aktiviert den Erkennungs-Bot. Ohne Schalter
wird kein Modell geladen. Initialisierung und Inferenz finden innerhalb der
regulären überwachten Bildkonvertierung statt und bezahlen deren bestehendes
Gesamtbudget mit. Der Modellzustand und bildgebundene Vorschläge werden innerhalb
eines Workers wiederverwendet. Produktionsworker verschiedener Bilder teilen
keinen warmen Modellzustand.

Der Erkenner liefert Klassen, Pixelpositionen und Konfidenzen für mehrere
Regionen. Die analytische Regionserzeugung erhält getrennte kleine Komponenten,
unterdrückt Lochkonturen und ergänzt horizontal gruppierte Regionen für Text.
Sie ist keine allgemeine Instanzsegmentierung: Verbundene Objekte und Text auf
gefüllten Scheiben können bereits hier verloren gehen. Klassifikation eines
Ausschnitts allein beweist deshalb keine vollständige Szenenerkennung.

Sichere Kreis-/Rechteckvorschläge ergänzen tatsächlich die Kandidatenbildung
des vorhandenen Grundformszenenfits. Dessen ursprüngliche analytische
Alternativen bleiben verfügbar. Anzahl, Negationen, Anordnung, lokale Objekt-
und globale Pixelprüfungen bleiben unverändert. Dreiecks-/Linien-/Textvorschläge
werden beobachtet, erzeugen in diesem begrenzten Szenenanschluss aber noch
keine neuen allgemeinen SVG-Topologien. Das ist weiterhin GENERAL-SCENE-01.

Konfiguration, Modellhash, Initialisierungs-/Inferenzzeit, Vorschläge und
Szenenverwendung stehen in der Komponentenbeobachtung. Ein beschädigtes oder
unpassendes Modell führt mit protokolliertem Fehler zur analytischen Alternative.
Ein hart beendeter Worker hat eventuell nur den Konfigurationsnachweis;
fehlende Abschlusszähler werden nicht als Nullaufwand interpretiert.

## Vorab festgelegter Versuchsaufbau

`tools/train_neural_elements.py` erzeugt 720 unterschiedliche synthetische
Quellfamilien mit analytischen Zeichenoperationen. Ganze Familien werden
**vor** Größen-/JPEG-Augmentation aufgeteilt: 480 Training, 120 Entwicklung,
120 synthetischer Holdout. Zwei Varianten je Familie ergeben 960/240/240
Ausschnitte. Auch Textquellstrings sind zwischen diesen Partitionen getrennt.
Trainingsseeds: 17, 42, 101; 35 feste Epochen ohne Auswahl anhand realer Ergebnisse.

Alle realen Daten bleiben außerhalb des Trainings. Sechs reale Katalogfamilien
werden als unabhängiger Prüfbestand kopiert und von Hand mit Klassen und
Positionen markiert: rF-, Lux-, M-, Q- und P-Scheibe sowie Ventil mit M-Scheibe.
Die Näherungsboxen werden vor der realen Modellauswertung eingefroren;
Zuordnung verlangt mindestens 0,5 IoU und 0,8 Konfidenz. Diese Annotationen
sind ein begrenzter Prüfbestand und kein allgemeiner Katalog-Ground-Truth.

Sechs neue Szenen mit ein bis drei getrennten Umrissen, darunter vertikale
Anordnungen, prüfen mehrere Instanzen. Ellipse und Dreieck bleiben als für die
allgemeine Szenenbildung unzureichend unterstützte Fälle im Nenner.

`tools/run_neural_elements.py` friert Raster, Beschreibungen, Annotationen und
Entscheidungskriterien vor Training und CLI-Messung ein. Jeder der 14 Fälle
wird pro Seed mit und ohne Netz durch die echte CLI konvertiert: **84 Versuche**,
jeweils fünf Sekunden ohne Verlängerung. Arme wechseln ihre Reihenfolge;
Inputs, Ausgaben und Caches sind getrennt. Modellhashes, geladene Workerquellen,
Renderereignisse, Speicher und Bild-/Batchzeiten werden aufgezeichnet.
Referenz-SVG-Lesezugriffe sind in den CLI-Prozessen gesperrt.

Die gespeicherten SVGs werden unabhängig erneut gerendert. Unveränderte strenge
Pixel-/Komplexitätsgrenzen und separate Text-/Ventil- beziehungsweise
Objektzahl-/Positions-/Formklassenprüfungen entscheiden über die Freigabe.
Fehlende Ausgaben bleiben Fehler. Die Verifikation verwirft veränderte Modelle,
Quellen, Zuordnungen, Telemetrie, Budgets, Qualitätswerte und doppelte oder
fehlende Messzellen.

Eine allgemeine positive Qualitätsentscheidung verlangt vorab mindestens acht
unabhängige reale Familien und einen positiven konservativen 95-%-Nachweis.
Seeds vervielfachen die Familienzahl nicht. Diese erste Machbarkeitsprüfung mit
sechs realen Familien kann diesen positiven Nachweis nicht erreichen. Sie kann
aber einen konkreten ungeeigneten Kandidaten aussortieren. Zeit-/Qualitäts-
Gleichwertigkeit wird aus fehlender Signifikanz ausdrücklich nicht abgeleitet.

## Ergebnis und Entscheidung

| Unabhängige CLI-Freigaben | Analytisch | Mit CNN |
| --- | ---: | ---: |
| Reale Familien, drei Seeds | 15/18 | 15/18 |
| Neue Grundformszenen | 18/18 | 18/18 |
| Unzureichend unterstützte Szenen | 0/6 | 0/6 |
| Gesamt | **33/42** | **33/42** |

78 der 84 Versuche speichern eine SVG; 66 bestehen alle unabhängigen Prüfungen.
Der Lux-Fall erreicht in beiden Armen bei allen drei Seeds die Fünfsekundengrenze
ohne gültige Ausgabe. Diese sechs Abbrüche bleiben enthalten. Bei den drei
neuronalen Abbrüchen fehlt der vollständige Inferenzabschlussnachweis; sie sind
zensierte Beobachtungen, keine Belege für ein nicht ausgeführtes Netz.

Auf synthetischen Ausschnitten erreichen die drei Modelle 97,5 %, 97,1 % und
97,9 % Klassifikationsgenauigkeit. Auf den neuen synthetischen Mehrinstanzszenen
werden 36/36 erwartete Elemente über die drei Modelle korrekt zugeordnet.
**Auf den realen Rasterfamilien gelingt dagegen keine der 45 erwarteten
Klassen-/Positionszuordnungen bei der eingefrorenen Konfidenzschwelle.**
Zwölf zusätzliche hochsichere, nicht passende Regionenvorschläge werden
gesondert gezählt. Das ist ein klarer Unterschied zwischen synthetischem
Klassifikationserfolg und realer Elementdetektion.

Die reale Schwäche betrifft gefüllte Scheiben, kleine Schrift und verbundene
Objekte: Die verwendete Vordergrundmaske liefert dort teils das ganze Symbol
statt innerer Text-/Formregionen; die Trainingsverteilung enthält Umrisse,
jedoch keine entsprechenden realen Füllungen. Ein bloßes Senken der
Konfidenzschwelle oder Qualitätsgrenzen wäre dafür keine belastbare Korrektur.

Im CLI-Lauf werden 36 zusätzliche neuronale Szenenstarts erzeugt, jedoch keiner
als beste vollständige Szene ausgewählt. Die 18 gepaarten realen Versuche
zeigen keinen zusätzlichen Erfolg und keinen Verlust; 14 gespeicherte reale
Ausgaben sind zwischen den Armen bytegleich. Das belegt keine allgemeine
Gleichwertigkeit. Median der realen Bildzeit: 0,703 s analytisch, 0,719 s mit
Netz; p95 rund 5,00 s in beiden Armen einschließlich der Abbrüche. Der kleine
Bestand begründet keine Geschwindigkeitsaussage.

Bei den vollständig protokollierten Netzaufrufen beträgt der Median der
Initialisierung etwa 0,93 ms, der Inferenz etwa 8,58 ms. Die Bildzeiten enthalten
den gesamten Workerstart. Spitzen-RSS der realen Worker: etwa 71,8 MB analytisch
und 72,3 MB mit Netz; native Imports sind enthalten, keine kausale isolierte
Speicherzuordnung. Zehn zusätzliche Inferenzwiederholungen pro Prüfbild messen
den warmen Detektor separat; sie sind keine warmen Produktions-CLI-Messungen.

**Entscheidung:** Diesen Modellstand außerhalb des Standardpfads behalten.
Es gibt keinen belegten Qualitätsgewinn und keinen freigegebenen Grund,
analytische Erkenner abzuschalten. Alle 377 archivierten Paare bleiben
hashgleich. Die offenen Arbeiten IDO-19/IDO-21, GENERAL-SCENE-01 und
SEARCH-DEADLINE-COMPAT werden nicht pauschal geschlossen.

## Reproduktion und Folgearbeit

Die abschließende betroffene Regression besteht mit **283 Tests**, einschließlich
eines tatsächlich blockierten Inferenzaufrufs im überwachten Spawn-Prozess.
Der Test weist den Eintritt in die Inferenz nach und prüft den rechtzeitigen
Abbruch ohne veröffentlichte Teil-SVG. Ein weiterer Integrationstest entfernt
gezielt den analytischen Szenenstart und verlangt eine unabhängig geprüfte
SVG aus dem neuronalen Positions-/Klassenvorschlag. Falsche hochsichere Klassen
dürfen weder Beschreibungsgrenzen umgehen noch analytische Alternativen
verwerfen. Syntax-, CLI- und Hardcoding-Prüfungen ergänzen die Regression;
ein vollständiger Repository-Testlauf ist hier nicht erfolgt.
Der für CI vorgesehene Smoke-Lauf wurde lokal zusätzlich ausgeführt und
unabhängig verifiziert: sechs Versuche, sechs SVGs, vier vollständige Freigaben,
drei beobachtete Netzaufrufe und weiterhin 377 unveränderte Archivpaare.

```powershell
.venv/Scripts/python.exe -m tools.run_neural_elements --output-dir .tmp/neural-study --work-dir .tmp/neural-study-work
.venv/Scripts/python.exe -m tools.run_neural_elements --verify-only --output-dir .tmp/neural-study
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/neural-tests tests/test_neural_elements.py
```

Die Modelle sind unter `artifacts/evaluation/neural_elements_v1/models/`
erhalten; eine normale Konvertierung kann sie ausdrücklich mit
`--neural-elements-model artifacts/evaluation/neural_elements_v1/models/model-17.json`
aktivieren. Der Standard bleibt unverändert analytisch. Modelle, Manifest,
Prüfzahlen und kompakte Zusammenfassung werden versioniert; Rohdaten und
vollständige Berichte bleiben lokal. Ein frischer Checkout erzeugt vor
`--verify-only` einen eigenen Lauf. CI trainiert einen Seed, prüft drei echte
CLI-Gegenproben und lädt den vollständigen Nachweis hoch. Das ersetzt keine
breite reale Abnahme; ein entfernter CI-Lauf wurde hier nicht gestartet.

Der erste Vorlauf liegt unter `.tmp/neural-evidence-v1`: Er hatte doppelte
Innenkonturen bei kleinen Ringen und erfasste Inferenz nur für den engeren
Nicht-Composite-Pfad. Nach Korrektur der Regionenerzeugung und Anschluss vor
der allgemeinen Iterationspipeline wurde der vollständige definitive Lauf
unter `.tmp/neural-evidence-v2` wiederholt. Reale Daten wurden dabei nicht zum
Training oder zur Schwellenanpassung verwendet.

Nächstes dokumentiertes Paket: **NEURAL-ELEMENTS-REAL-02**. Zuerst reale
Regionen-/Instanzfehler inventarisieren und unabhängig markieren, vor jeder
Augmentation ganze Quellfamilien auf reales Training, Entwicklung und einen
neuen gesperrten Holdout aufteilen. Gefüllte Flächen, verschachtelte Schrift,
verbundene und kleine Objekte sowie unbekannte Formen abdecken. Mindestens
acht unabhängige reale Abnahmefamilien und mehrere Trainings-/Suchseeds
vorsehen; die hier bereits betrachteten sechs Familien sind künftig nur
Entwicklungsdaten. Danach eine geänderte Regionenerzeugung und einen zweiten
kleinen Detektor bei gleichem Budget gegen diesen unveränderten analytischen
Standard prüfen. Keine Standardaktivierung ohne positiven End-to-End-Nachweis.
