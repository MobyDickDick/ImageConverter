# NEURAL-ELEMENTS-REAL-02 – reale Regionen und zweiter optionaler Detektor

Stand: 19. Oktober 2026. Das dokumentierte Folgepaket nach dem ersten
CNN-Versuch untersucht reale Trainingsregionen, eine veränderte
Regionserzeugung und einen zweiten kleinen Detektor im tatsächlichen
CLI-Pfad. **Eine bessere Regionsabdeckung allein rechtfertigt keine
Standardaktivierung.** Die analytischen Erkenner und sämtliche bestehenden
Qualitätsgrenzen bleiben erhalten.

## Vorab eingefrorener Prüfbestand

`config/neural_real_regions.json` enthält 27 unveränderte Originalraster aus
dem Katalog mit 63 markierten Regionen. Die Positionen wurden anhand
vergrößerter Raster-Kontaktbögen visuell markiert, unabhängig von beiden
Detektoren und ohne Referenz-SVG. Es handelt sich um Näherungsboxen des
bearbeitenden Coding-Agenten, nicht um einen extern doppelt annotierten
Segmentierungsdatensatz. Verschachtelte Regionen dürfen sich überlappen.
Schriftregionen bedeuten keine erkannten Zeichen; komplexe Formen außerhalb
des Klassenvokabulars sind ausdrücklich `unknown`.

| Partition | Originalraster | Quellfamilien | Regionen |
| --- | ---: | ---: | ---: |
| Reales Training | 11 | 9 | 24 |
| Entwicklung | 6 | 6 | 15 |
| Neuer gesperrter Abnahmebestand | 10 | 10 | 24 |

Die sechs Familien aus NEURAL-ELEMENTS-01 sind ausschließlich Entwicklung.
Training und neue Abnahme teilen keine Quellfamilie oder Bildbytes.
Quadratische Buchstabenkellen werden trotz verschiedener Buchstaben als
eine Trainingsfamilie behandelt. Größen-, Farb- oder Drehvarianten einer
Quelltopologie dürfen nicht auf andere Partitionen verteilt werden. Der
Trainer öffnet nur die elf realen Trainingsraster; eine Regression verbietet
explizit Lesezugriffe auf Entwicklung und Abnahme.

Die zehn neuen Abnahmefamilien sind Pumpe, Sehnen-/T-Scheibe, Spiralscheibe,
Warnzeichen, verschachtelte Flammen, Haus, freier Pfeil, Bogen mit Schaft,
T-Verzweigung und Kurvendiagramm. Sie sind neu für diesen Netzversuch; ihre
grundlegenden Konvertierungsverfahren existierten bereits. Das ist kein
Nachweis bisher unbekannter allgemeiner Szenentopologien.

Manifest, Boxen, Familien, 0,8-Konfidenzschwelle, mindestens 0,5 Box-IoU,
Trainingsdauer und Qualitätsentscheidung werden vor Training/Auswertung
festgeschrieben. Alle drei Modelle werden vor der ersten
Abnahme-Inferenz trainiert. Nach Betrachtung des Abnahmebestands wurden
weder Modelle noch Regionsparameter oder Qualitätsgrenzen angepasst.

## Umsetzung und tatsächlicher Runtime-Anschluss

`tiny_elements_cnn_v2` behält die kleine Architektur mit 1.830 Parametern und
den sechs Klassen Kreis, Rechteck, Dreieck, Linie, Text und unbekannt.
Es nutzt reale Ausschnitte, deren Größen-/JPEG-Augmentation erst nach der
Familientrennung erfolgt, sowie ausschließlich die synthetischen
Trainingsfamilien des Vorgängers und deren zusätzliche gefüllte Varianten.
1.584 Trainingsausschnitte, 35 feste Epochen und die Trainingsseeds
17, 42 und 101 ersetzen jede
Modellwahl am Holdout. NumPy/OpenCV genügen; neue Frameworks sind nicht nötig.

Die zweite Regionserzeugung prüft mehrere feste Helligkeits- und Farbkanalstufen,
innere Konturen sowie horizontal gruppierte kleine Regionen. Sie kann dadurch
helle Schrift innerhalb gefüllter Flächen vorschlagen. IoU-Deduplizierung und
höchstens 128 Vorschläge begrenzen den Inferenzumfang. Sie ist weiterhin keine
allgemeine Segmentierung verbundener Instanzen.

Die Modellkennung wählt die Regionserzeugung. Alte v1-Modelle behalten ihren
alten Weg. Ohne `--neural-elements-model` wird weiterhin kein Netz geladen.
Initialisierung, Inferenz, Rückfall bei ungültigem Modell und bildgebundener
Cache liegen im bestehenden überwachten Bildbudget. Der tatsächliche
Szenenanschluss bleibt der vorhandene begrenzte Kreis-/Rechteckweg: Analytische
Alternativen überleben, Beschreibung und lokale/globalen Gates bleiben Pflicht.
Ein Integrationstest entfernt den analytischen Start und verlangt eine
unabhängig geprüfte SVG aus einem v2-Vorschlag. Gefüllte komplexe Szenen
bekommen durch eine Klassenvorhersage noch keinen neuen SVG-Generator.

## Unabhängige Messung

`python -m tools.run_real_neural_elements` kombiniert drei Trainingsseeds mit
drei Suchseeds vollständig. Je Kombination werden dieselben zehn Fälle mit
und ohne Netz durch die echte überwachte `semantic-only`-CLI konvertiert:
**180 Versuche, 90 Paare**, fünf Sekunden pro Bild ohne Verlängerung.
Die Armreihenfolge wechselt, Eingaben/Ausgaben/Caches sind isoliert,
Referenz-SVG-Lesezugriffe gesperrt. Die Seeds erhöhen nicht die Zahl der
unabhängigen Familien.

Gespeicherte SVGs werden erneut gerendert und gegen die unveränderten strengen
globalen Pixel-/Komplexitätsgrenzen geprüft. Zusätzlich muss jede markierte
Region dieselben festen lokalen Grenzen wie der Grundformszenenvertrag
bestehen: normalisierter MSE höchstens 0,01, Vordergrund-MSE höchstens 0,04,
Vordergrund-IoU mindestens 0,85 und Kantenausrichtung mindestens 0,72.
Der Prüfer verwendet weder Regionsvorschläge noch Netzklassen. Diese
Rasterlokalprüfung ist ein zusätzlicher Schutz für kleine/verschachtelte Objekte,
kein allgemeiner OCR- oder semantischer Instanzbeweis. Die Abnahme der
vorhandenen Archivpaare wird dadurch nicht nachträglich umdefiniert.

Ein Kontrolltest entfernt ein kleines Innenobjekt und verlangt eine Ablehnung.
Fehlende Ausgaben bleiben im Nenner. Der Verifikationsmodus prüft die
vollständige Train-/Suchseed-Matrix, Modellzuordnung, Input-/SVG-Hashes,
beobachtete Runtime-Schalter, Telemetrie, erneute Detektion und lokale Gates.
`--resume` übernimmt ausschließlich vollständige unabhängig verifizierte
Versuchsblöcke bei gleichen Rasterdaten, Modellen und Runtime-Quellen.

## Befund und Grenzen

Die von Klassen unabhängige Box-Inventur zeigt folgende reine Regionsabdeckung;
die Klasse wird an dieser Stelle noch nicht bewertet:

| Partition | Vorher | Mehrstufig |
| --- | ---: | ---: |
| Training | 13/24 | 20/24 |
| Entwicklung | 6/15 | 13/15 |
| Neue Abnahme | 15/24 | 21/24 |

Die tatsächlich klassifizierten Vorschläge werden separat mit
Klasse/Position, kleinen Instanzen, falscher hoher Konfidenz und doppelten
hochsicheren Vorschlägen ausgewiesen. Trainingsklassifikation ersetzt diese
Messung nicht. Die vielen falschen hochsicheren Vorschläge begrenzen den
praktischen Nutzen des Kandidaten.

Die drei Modelle treffen auf den neuen Originalrastern 25 von 72 erwarteten
Klassen-/Positionszuordnungen (24 Regionen × drei Modelle), bei kleinen
Regionen 3/24. Gleichzeitig entstehen 1.369 hochsichere, nicht passende
Vorschläge und sieben zusätzliche Duplikate. 73 dieser nicht passenden
Vorschläge sind als `unknown` klassifiziert, 1.296 behaupten eine bekannte
Klasse; darunter fallen 1.106 Rechteckvorschläge. Auf den sechs Entwicklungsfamilien
werden 17/45 Regionen getroffen, gegenüber keiner beim ersten, anders
trainierten Kandidaten. Wegen der geänderten Annotation einer P-Scheibe ist
das kein exakter gepaarter Modellvergleich. Der reine synthetische
Klassifikationserfolg des Vorgängers hatte diese realen Probleme verdeckt.

| Vollständige unabhängige CLI-Freigaben | Analytisch | Mit v2-CNN |
| --- | ---: | ---: |
| Zehn reale Abnahmefamilien × neun Seed-Kombinationen | **71/90** | **72/90** |
| Gespeicherte SVGs | 89/90 | 89/90 |

178 SVGs aus 180 Versuchen werden unabhängig nachgemessen; 143 bestehen
alle Gates. 88 der 90 Paare liefern bytegleiche SVGs. In 89 beobachteten
Netzaufrufen entstehen **keine** zusätzlichen Szenenkandidaten für diese
gefüllten/komplexen Fälle; keiner wird ausgewählt. Der aktuelle Szenenanschluss
kann die besseren Regionen deshalb nicht in neue Topologien umsetzen.

Der eine zusätzliche vollständige Netz-Erfolg ist die Flamme bei
Trainingsseed 101/Suchseed 42: analytisch entsteht innerhalb von 5,031 Sekunden
keine gültige Ausgabe. Die übrigen acht analytischen Flammenversuche bestehen.
Das ist ein beobachteter gepaarter Unterschied, aber kein belastbarer
Qualitätsgewinn: keine zusätzliche Szene, zehn unabhängige Familien und ein
konservatives 95-%-Intervall mit Halbbreite 0,859 bei einer beobachteten
Differenz von 0,011. Die vorab festgelegte Übernahmeregel bleibt negativ.

Eine weitere Auffälligkeit bleibt ausdrücklich im Nenner: Der neuronale
Hausversuch bei Trainingsseed 42/Suchseed 17 wurde rund 594,688 Sekunden
unterbrochen, bevor ein Workerstart beobachtet werden konnte. Er liefert
weder SVG noch Schalter-/Inferenzbeleg. Der neue Verifikationsmodus erlaubt
diesen fehlenden Start ausschließlich als ausdrücklich zensierten,
unbeobachteten Fehlschlag ohne Ausgaben oder erfundene Nullkosten; bestehende
Prüfungen bleiben standardmäßig strikt. Er zählt nicht als nachgewiesen
ausgeführtes Netz. Sobald ein solcher unbeobachteter Start enthalten ist,
sperrt die Entscheidungsregel jede Standardübernahme, auch bei nominell
positiven Erfolgszahlen; eine Regression prüft genau diesen Gegenfall.
Diese konservative Wiederaufnahmesperre wurde nach der beobachteten
Unterbrechung ergänzt; keine Messzelle wurde ersetzt und kein Gate gelockert.
Die konfigurierten Fünfsekundenbudgets sind damit kein
Beleg für eine durchgängig eingehaltene Wallclock-Grenze bei dieser
Umgebungsunterbrechung. Der andere fehlende Output ist der oben genannte
reguläre analytische Flammen-Timeout.

Median der beobachteten Modellinitialisierung: 0,89 ms; Inferenz: 14,81 ms.
Bildzeit-Median: rund 1,602 s in beiden Armen; p95 4,489 s analytisch und
4,510 s mit Netz. Spitzen-RSS der Worker rund 88,3/88,7 MB einschließlich
Imports; Renderaufrufe 48.780/48.506. Dies sind deskriptive Rohbeobachtungen,
keine nachgewiesene Zeit-/Speichergleichwertigkeit. Alle **377 Archivpaare**
bleiben hashgleich.

Die zusätzlichen lokalen Prüfungen erkennen unter anderem Abweichungen an
den kleinen Hausfenstern und der Diagrammkurve. Ein global guter Rasterwert
allein zählt dort nicht als vollständige Freigabe.

Die analytische Standardkonvertierung bleibt aktiv. Das Netz erhält keine
allgemeine Gleichwertigkeits- oder Geschwindigkeitsfreigabe; ein positiver
konservativer Familiennachweis ist Voraussetzung für eine Standardübernahme.
Initialisierung/Inferenz, warme reine Detektorwiederholungen, Worker-RSS,
Renderzahlen und gesamte Bild-/Batchzeiten bleiben in der Rohmessung getrennt.
Parallele lokale Regression und eine auffällige Unterbrechung in einem
separaten Smoke-Training machen insbesondere Trainings-/Laufzeitvergleiche
ungeeignet für eine kausale Geschwindigkeitsaussage.

## Reproduktion und nächste Arbeit

```powershell
.venv/Scripts/python.exe -m tools.run_real_neural_elements --output-dir .tmp/neural-real-study --work-dir .tmp/neural-real-work
.venv/Scripts/python.exe -m tools.run_real_neural_elements --verify-only --output-dir .tmp/neural-real-study
.venv/Scripts/python.exe -m pytest -q tests/test_real_neural_elements.py tests/test_neural_elements.py
```

`artifacts/evaluation/neural_real_regions_v2/` bewahrt Manifest,
Regionsinventur, Modelle und kompakte Nachweise auf. Generierte Originalkopien,
Rohtelemetrie und SVGs bleiben lokal und werden für CI als Artefakt hochgeladen.
Ein frischer Checkout erzeugt vor `--verify-only` einen eigenen Lauf.
Der CI-Smoke trainiert die drei festen Modelle und prüft zwei echte
Rasterfälle mit einem Such-/Trainingsseed in beiden Armen. Er ersetzt keine
breite reale Abnahme.

Eine reguläre Konvertierung kann einen erhaltenen v2-Kandidaten ausdrücklich
mit `--neural-elements-model artifacts/evaluation/neural_real_regions_v2/models/model-17.json`
verwenden. Ohne diesen Schalter bleibt sie analytisch. Die kompakte Ablage
enthält rund 200 KB für die drei Modelle einschließlich Trainingsprotokoll
und Trainingsmessung. Syntax-, CLI-Help- und Hardcoding-Prüfung bestehen;
die betroffene Regression besteht mit **126 Tests**. Der separat lokal
ausgeführte und erneut verifizierte CI-Smoke besteht mit vier SVGs aus vier
Versuchen. Ein entfernter CI-Lauf wurde hier nicht gestartet.

Der zu Arbeitsbeginn gesammelte vollständige Standard-/Baseline-Lauf
(`python -m pytest -q`) endet mit **3.546 bestandenen und 30 übersprungenen
Tests**, ohne Fehler. Er umfasst den damaligen Testbestand; das neu angelegte
Testmodul und der endgültige v2-/Entscheidungsstand sind durch die anschließend
ausgeführte abschließende Regression mit 126 Tests abgedeckt. Die schweren
optionalen Module bleiben gemäß dem vorhandenen Standardprofil ausgenommen.
Die Gesamtdauer von rund 116 Minuten enthält lange Umgebungsunterbrechungen
und ist keine Konvertierungs-Laufzeitmessung. Lokale Protokolle:
`.tmp/real02-full-tests.log`, `.tmp/real02-target-final2.log` und
`.tmp/real-neural-preserved-final.log`.

Das begrenzte reale Detektorexperiment ist abgeschlossen; die produktive
Abnahme von NEURAL-ELEMENTS-01 bleibt offen. Nächste Architekturarbeit ist
der bereits offene **GENERAL-SCENE-01**: unabhängige Instanzprüfung und
gemeinsame Szenenbildung für gefüllte/verschachtelte Kandidaten. Die zehn
hier ausgewerteten Familien sind für weitere Modellauswahl künftig ebenfalls
Entwicklungsdaten; eine neue Netzabnahme braucht neue gesperrte Familien.
SEARCH-DEADLINE-COMPAT und IDO-19/IDO-21 bleiben offen.
