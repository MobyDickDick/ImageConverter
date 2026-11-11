# Warum der erhaltene Kataloglauf wenig befriedigende Ergebnisse liefert

Audit vom 11.11.2026. Untersucht wurde der vom Benutzer bestätigte Lauf
`catalog-20261110T201918Z-3a5bfe5a`, Seed `913823148`, vom 10.11., ungefähr
21:19–21:41 Uhr Schweizer Zeit. Der frühere längere Lauf wurde überschrieben;
über dessen Ergebnis oder Verbesserungskurve ist keine belastbare Aussage möglich.

Während des Auditabschlusses begann im gleichen Ausgabeordner zusätzlich der
neue Lauf `catalog-20261111T121521Z-d7a16496` vom 11.11., 13:15 Uhr Schweizer
Zeit. Er ersetzte die fünf Übersichtsdateien und wird hier ausdrücklich nicht
mitgezählt. Die zuvor erstellte Auswertung samt ursprünglichen Hashes bleibt
erhalten. Alle 152 Einzeldateien des untersuchten kurzen Laufs — 38 Eingaben,
38 SVGs, 38 Worker- und 38 Komponentenprotokolle — konnten noch unverändert
mit Hashprüfung unter `.tmp/catalog-run-audit/frozen-20261110T201918Z/`
gesichert werden. Die ursprünglichen fünf Rohübersichten selbst sind nicht
mehr verfügbar; ihre zuvor erhobenen Messdaten stehen im kompakten Nachweis.

**Hauptbefund:** Es gibt viele echte Rechenversuche, aber der größte Teil
optimiert einen bereits festgelegten, häufig unvollständigen SVG-Aufbau.
Eine breite Suche nach verschiedenen vollständigen Bildkonstruktionen und
ein dauerhaftes selbständiges Erlernen neuer Lösungsverfahren fehlen in
diesem Lauf. Weitere Laufzeit allein beseitigt diesen Engpass nicht.

## Messung am gespeicherten Lauf

| Beobachtung | Ergebnis |
| --- | ---: |
| Ausgewählte Katalogeingaben | 1.787 |
| Begonnene Eingaben | 41 |
| Gespeicherte Ergebniszeilen/SVGs | 38 |
| Explizite Prozess-/Semantikfehler | 2 |
| Begonnen ohne gespeichertes Endergebnis | 1 |
| Vom Konverter vollständig modellbestätigt | 10/38 |
| Unabhängig erneut geprüfte reine Pixelpässe | 13/38 |
| Adaptive Nachoptimierung eines vorhandenen SVG-Aufbaus | 28/38 |
| Modellbestätigte Ergebnisse dieser 28 Nachoptimierungen | 0/28 |
| Gemeldete Renderauswertungen | 60.292 |
| Neue Bot-Parametervorschläge | 77.895 |
| Davon gültig / zurückgewiesen | 41.673 / 36.222 |
| Bot-Neustartereignisse | 544 |
| Median der gemeldeten Bildlaufzeit | 32,961 s |
| Ergebnisse mit mindestens 30 s Bildlaufzeit | 36/38 |
| Ereignisse der gemeinsamen strukturellen Szenensuche | 0 |
| Beschreibungen, die ihren derzeitigen Mischszenenvertrag erfüllen | 0/38 |
| Eingaben mit eingeschaltetem neuronalen Detektor | 0/38 |

Die 13 Pixelpässe sind keine nachträgliche menschliche oder vollständige
Objektabnahme. Drei davon bleiben ausdrücklich Entwürfe: `AC0251_2`,
`AC0722_1_S` und `GE9001_1S`. Die zehn bestätigten Ausgaben stammen aus
vorhandenen Spezialwegen für Pfeil, Spirale, Flamme und zwei Arten
Linien-/Verlaufsgeometrie. Sie sind kein Beleg, dass das System diese
Verfahren während des Laufes neu entwickelt hätte.

Die beiden expliziten Fehler sind ein Beschreibungswiderspruch bei `SE0113`
und ein Timeout ohne gesichertes Ergebnis bei `GE9901_W`. Für dessen
abgebrochenen Worker ist die tatsächlich geleistete interne Suche nicht
vollständig belegt. `GE1102_L` wurde anschließend begonnen, besitzt im
erhaltenen Protokoll aber keinen Abschluss. Der Lauf blieb im `initial_pass`.
Diese kleine zufällige Teilmenge ist keine Erfolgsquotenmessung des gesamten Katalogs.

Maschinenlesbare Messwerte, Einzelfälle, Eingabe-/Ausgabe-/Protokollhashes und
Gegenproben stehen im [Nachweis](../artifacts/evaluation/catalog_search_audit_v1/summary.json).
Es wurden die diesem Lauf zugeordneten 38 Worker-/Komponentenprotokolle
ausgewertet; die wesentlich größere globale Suchdatei und ältere Workerdateien
wurden nicht als zusätzliche Versuche dieses Laufes gezählt.

## 1. Die sechs Bots verändern überwiegend dieselbe Konstruktion

Die Bots besitzen verschiedene Koordinatenfolgen, Schrittweiten und
Mehrparameter-Neustarts. Ihre Arbeit ist real: Sie erzeugen neue Vorschläge,
tauschen bessere Werte aus und starten nach Stagnation neu. Sie erfinden
dabei keine neuen Suchalgorithmen oder unbekannten Objektarten.

Bei 28 Bildern ist die einzige protokollierte adaptive Registrierung
`native_svg_continuation`. Dieser Pfad variiert gemeinsame Platzierung,
gleichmäßige Skalierung, vorhandene Strichbreiten, Farben und Verlaufsstopps.
Die Anzahl, Art und Anordnung der vorhandenen SVG-Elemente bleiben strukturell
fest. Vorgelagert können wenige vorhandene Beschreibungs-/Wahrnehmungsmodelle
verglichen worden sein; die folgende Botsuche erweitert deren Konstruktion nicht.

Das ist im [Vektornachoptimierer](../src/iCCModules/imageCompositeConverterVectorPolish.py)
direkt nachprüfbar: `seed`, `geometry`, `valid()` und `build()` parameterisieren
vorhandene Elemente; neue Elemente werden nicht aus Restfehlern vorgeschlagen.
Die sechs Strategien im [Bot-Sucher](../src/iCCModules/imageCompositeConverterSearchBots.py)
arbeiten auf diesem Parametervektor.

Sichtbare Folgen in Original-/SVG-Vergleichen:

| Eingabe | Im Original vorhanden | In der gespeicherten neuen Ausgabe fehlend |
| --- | --- | --- |
| AC0030 | Zwei diagonale Kreuzlinien und kleine Markierung | Kreuzlinien und Markierung; im Wesentlichen bleibt die Verlaufsfläche |
| AC0552_1_M | Deutliche helle V-Linien im roten Rechteck | V-Linien |
| GE0043_L | Kalenderzahl 31 und tabellarische weiße Felder | Zahl und Tabellenstruktur |
| GE0202_S | Verzweigte sechsstrahlige Schneeflocke | Die gesamte Verzweigungsstruktur |
| GE9044_7S | Gebogene gelbliche Doppelstruktur | Kurven; übrig bleibt eine rechteckige Farbfläche |

Eine andere Farbe oder eine weitere globale Skalierung kann diese fehlenden
Elemente nicht herstellen. Das erklärt zugleich, warum ein niedrigerer
mittlerer Pixelfehler noch kein befriedigendes Symbol ergibt.

## 2. Die neue Struktursuche erreicht diese Eingaben nicht

Die zuletzt ausgebauten Strukturmodule besitzen reale Add/Remove/Replace-,
Gruppierungs- und Tiefenoperationen. Ihr Eingangsvertrag ist jedoch eng:
gezählte gefüllte Kreise/Rechtecke, ein explizit beschriebener äußerer
Verlaufscontainer und bestimmte Innen-/Überdeckungsrelationen.

Die erhaltenen Beschreibungen erfüllen im aktuell geprüften
[Mischszenenvertrag](../src/iCCModules/imageCompositeConverterMixedGradientScene.py)
**0/38** dieser Verträge. Entsprechend gibt es in den Laufprotokollen keine
`scene_hypothesis`- oder `structure_search_finished`-Ereignisse.
Die vielen positiven synthetischen Kompositionstests belegen daher bisher
vor allem die abgesicherten Teilfamilien. Sie messen nicht die Breitenwirkung
auf die hier tatsächlich laufenden Katalogsymbole.

Zusätzlich fehlen beim Kalender trotz vorhandener Beschreibung die
ausführbaren Bedingungen für Zahl und Tabelle. Andere Beschreibungen sind
selbst unzureichend oder unpassend: `GE9044_7S` wird beispielsweise als
hellgraues Quadrat beschrieben, während das Raster eine gebogene gelbliche
Struktur zeigt. Bessere Formmodelle und eine belastbare Umsetzung der
Beschreibungsmerkmale sind beide erforderlich; bloß alle Beschreibungen in
die enge Kreis-/Rechtecksprache umzuschreiben wäre keine allgemeine Lösung.

## 3. Dauerhaftes Lernen findet in diesem Modus nicht statt

Der Lauf verwendet `semantic-only`. Die
[CLI-Konfiguration](../src/iCCModules/imageCompositeConverterCli.py) setzt
`allow_memory` nur im Modus `standard`. Das
[Suchportfolio](../src/iCCModules/imageCompositeConverterSearchPortfolio.py)
liest hier keine gelernte Strategiereihenfolge aus früheren Läufen.
Blackboards erhalten Wissen innerhalb des aktuellen Bild-/Modellkontexts;
sie bilden kein dauerhaftes Repertoire neuer Bildkonstruktionen.

Selbst die vorhandene persistente Funktionalität dient überwiegend der
Reihenfolge bereits bekannter Verfahren und einzelnen validierten
Kurztextvarianten. Sie ist kein automatischer Aufbau neuer Formgeneratoren.
Der neuronale Detektor war in allen 38 Komponentenprotokollen deaktiviert;
es gab in diesem Lauf keine protokollierte Modelltrainings- oder
automatische Codeverbesserungsschleife.

## 4. Der Katalogablauf verschiebt zusätzliche Qualitätsrunden sehr weit

Zwei zusätzliche Katalog-Qualitätsrunden waren konfiguriert. In
[der Orchestrierung](../src/iCCModules/imageCompositeConverterRemaining.py)
folgen sie jedoch erst **nach** dem vollständigen Erstdurchlauf aller
ausgewählten Bilder. Der erhaltene Lauf erreicht diese Stelle nicht:
kein `quality_threshold_resolved`, keine Katalog-Qualitätsrunde, Checkpoint
weiterhin `initial_pass`.

Das ist von den bereits gelaufenen inneren Botversuchen zu unterscheiden.
Eine kürzere Sitzung kann viele halbfertige Entwürfe erzeugen und die
zusätzlichen bildübergreifend geplanten Wiederholungen trotzdem nie erreichen.
Wenn alle 1.787 Bilder die 30-Sekunden-Mindestphase benötigten, würde allein
diese Phase rechnerisch rund 14,9 Stunden beanspruchen. Das ist eine bedingte
Aufwandsrechnung, keine Prognose des gesamten Kataloglaufs.

## 5. Die Berichte vermischen Entwürfe, Prozessfehler und aktuelle Fehlerwerte

`batch_failure_summary.csv` enthält zwei Prozess-/Semantikfehler. Daraus folgt
nicht, dass die übrigen Ergebnisse gelungen sind: 28 gespeicherte SVGs sind
nicht modellbestätigt. In der Bestlisten-CSV sind alle 38 `status`-Felder leer.
Der eindeutigere Status steht erst im JSON unter `search_satisfactory`.

Außerdem ist ein echter Reportingfehler nachgewiesen: Nach der
Vektornachoptimierung bleibt bei allen 28 betroffenen Zeilen `best_error`
aus dem vorherigen Fit erhalten. Die gespeicherten SVGs wurden anschließend
erneut gerendert; bei `GE9001_1S` beträgt der aktuelle mittlere absolute
Pixelfehler etwa **2,7956**, während `best_error` noch **19,6489** meldet.
`mean_delta2` stimmt dagegen mit dem gespeicherten SVG überein.

Die Ursache ist die nachträgliche SVG-Ersetzung im
[Artefaktschreib-Callback](../src/iCCModules/imageCompositeConverterIterationInitialization.py),
während der ursprüngliche Fit-Fehler als Rückgabewert in den
[Ergebnisbericht](../src/iCCModules/imageCompositeConverterConversionExecution.py)
gelangt. Die pauschale Angabe `actual_iterations=64` stammt bei fehlenden
Detailzählern außerdem aus dem angeforderten Budget; sie ist kein Nachweis
für 64 verschiedene Modellkonstruktionen.

## Gegenproben und faire Einordnung der Verbesserungen

Alle 28 Nachoptimierungen verbessern ihren eigenen frischen Startwert.
Die mediane MSE-Verbesserung beträgt rund **28,9 %**. Trotzdem erreicht keine
dieser 28 eine Modellfreigabe. Das bestätigt die Begrenzung des Suchraums,
statt fehlende Rechenarbeit zu behaupten.

Als kleine diagnostische Gegenprobe wurden ausschließlich aus den dunklen
Restpixeln von `AC0030` zwei lange Diagonalen mit Hough-Linienbestimmung
gewonnen und dem gespeicherten SVG hinzugefügt. Ohne weiteren langen
Parameterlauf sinkt der normalisierte MSE von **0,014801 auf 0,009740**,
also zusätzlich um **34,2 %**. Die Kantenmetrik verbessert sich von etwa
0,598 auf 0,681. Die strengen Kanten-/IoU-Gates bestehen damit weiterhin
nicht vollständig. Dies ist ein Ursachenexperiment für fehlende
Strukturvorschläge, keine fertige Konverterkorrektur oder neue Familienabnahme.
Die Originalausgaben wurden dabei nicht verändert.

Es gibt auch deutliche Erfolge: Der Pfeil `GE0032` und die Flamme `b_heating1`
werden gegenüber den im Git-Stand vorhandenen alten SVGs wesentlich besser
rekonstruiert. Für 17 vorhandene historische SVG-Vergleichspartner ergeben
sich 14 niedrigere, zwei höhere und ein unveränderter MSE. Einer der beiden
Rückgänge ist sehr klein. Die anderen 21 aktuellen Ausgaben besitzen dort
keinen Vergleichspartner. Der Git-Stand ist ausdrücklich **nicht** der
überschriebene vorherige Lauf und belegt deshalb keine Lernkurve zwischen
den beiden Benutzerläufen.

## Konsequenz für die nächsten Arbeiten

Der größte zu erwartende Nutzen liegt jetzt bei einer allgemeinen
Strukturerkundung im tatsächlich benutzten Fallbackpfad:

1. Mehrere unterschiedliche vollständige Konstruktionen erhalten und aus
   unerklärten Restbereichen native Linien, Liniengruppen, Text oder
   passende andere Primitive ergänzen bzw. ersetzen. Unterschiede der
   Konstruktion und Anzahl der Objekte explizit protokollieren.
2. Fehlende Merkmale lokal bewerten: Kreuz, V-Linien, Zahl/Tabelle und
   Schneeflockenäste dürfen nicht hinter einer großen gut passenden
   Hintergrundfläche verschwinden. Beschreibungsmerkmale und vorhandene
   Qualitätsgrenzen gemeinsam prüfen.
3. Kleine Gruppen von Bildern mit unmittelbarer Rückmeldung bearbeiten,
   bevor der ganze Katalog abgearbeitet wird. Die Strategien bei gleichem
   Gesamtbudget gegen den heutigen Fallback vergleichen.
4. Unveränderliche Laufordner, nachvollziehbare Kandidatenherkunft und
   validierte positive/negative Beispiele dauerhaft erhalten. Darauf kann
   eine überprüfbare Lern- und Auswahlsteuerung aufbauen. Bereits bekannte
   Verfahren neu zu sortieren reicht dafür nicht aus.
5. Parallel die zwei belegten Reportingfehler beheben: aktuelle SVG-Metriken
   atomar mit dem SVG übernehmen und Entwurf/Modellfreigabe/Prozessfehler
   sichtbar auseinanderhalten.

Die hier analysierten Bilder sind bereits bekannte Entwicklungsfälle.
Ein späterer Wirksamkeitsnachweis benötigt zusätzlich getrennte neue reale
Prüffälle. Weitere enge Randfallpakete und reine Laufzeitverlängerungen
belegen die gewünschte breite selbständige Verbesserung nicht.

Der Audit hat keinen neuen Kataloglauf gestartet und weder Produktionscode
noch vorhandene Konvertierungsergebnisse verändert. Ein lokales visuelles
Vergleichsblatt und die diagnostische SVG-Gegenprobe liegen unter
`.tmp/catalog-run-audit/`. Nur der kompakte Nachweis und dieser Bericht
werden zur Versionierung bereitgestellt.
