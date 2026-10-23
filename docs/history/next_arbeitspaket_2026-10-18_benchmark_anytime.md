# BENCHMARK-ANYTIME-01 – Qualitätskurven der Produktionskonvertierung

Arbeitsbranch: `codex/benchmark-anytime-01-2026-10-18`.
Verglichen werden der eingefrorene Stand `00d48fe5c` vor SEARCH-SCHEDULER-02
und der übernommene Scheduler auf `90f8e7fee`. Dieses Paket ergänzt Messung
und Nachweise. Die Konvertierungsalgorithmen und Qualitätsgrenzen bleiben erhalten.

## Versuchsvertrag

`tools/run_anytime_benchmark.py` startet für beide Stände die echte überwachte
`semantic-only`-CLI mit genau 1, 5, 15 und 60 Sekunden Bildbudget. Die maximale
Zeit ist jeweils dieselbe Grenze; adaptive Verlängerungen können den Vergleich
nicht verschieben. Jeder Versuch erhält frische Rasterkopien, Ausgaben und
Caches. Suchseeds sind 17, 42 und 20261018. Die Reihenfolge der gepaarten
Eltern-/Schedulerläufe wechselt; alle Konvertierungen laufen nacheinander.

Die Kurve besteht aus **neuen Konvertierungen je Zeitgrenze**, nicht aus
nachträglich interpolierten Zwischenständen eines einzigen 60-Sekunden-Laufs.
Die Produktionsuhr umfasst Workerstart und Abschlussprüfungen. Batchstart,
Berichte und Prozessbereinigung werden zusätzlich als Batchdauer gespeichert.
Timeoutzeiten sind zensierte Beobachtungen, keine gemessenen Erfolgszeiten.
Median/p95 aller Versuche schließen diese Zeiten ein; Erfolgszeiten sind
zusätzlich separat ausgewiesen. p95 verwendet lineare Interpolation.

Die acht eingefrorenen Fälle umfassen zwei echte JPEGs (Dreiwegeventil mit
M-Scheibe und rF-Scheibe), ein neues grünes Hz-Symbol mit zwei inhaltlich
gleichen Beschreibungen, zwei neue gemischte Kreis-/Rechteckanordnungen mit
zwei bzw. drei Objekten sowie eine Ellipse und ein Dreieck als bisher in den
Scheduler-Nachweisen ungeprüfte Familien. Die neuen Szenen variieren Größe,
Farbe und Anordnungsachse. Das Hz-Paar hat identische Rasterbytes. Diese
Kontrollpaarung zählt ausdrücklich nicht als zwei unabhängige Bildfamilien.
Die neuen Fälle stammen aus analytischen Generatoren ohne Konverterhilfen;
ihre SVG-Texte werden nach dem Einfrieren nicht als Runtime-Eingabe gespeichert.

Der Elternlauf ersetzt ausschließlich die vier damals geänderten Suchmodule.
Alle übrigen Elternquellen werden gegen die aktuellen Dateien geprüft;
abweichende Baselines außerhalb dieses Umfangs werden abgewiesen. Damit
bleiben unveränderte Abhängigkeiten und Ressourcen an ihren Produktionspfaden.
Ein Bootstrapfehler darf den Vergleich nicht still auf den aktuellen Stand
zurückfallen lassen. Die geladenen Dateien werden zusätzlich in den
Spawn-Workern per SHA-256 gebunden, einschließlich unterschiedlicher
Eltern-/Scheduler-Suchmodule. Vollständige Quellhashes stehen im Bericht.

## Unabhängige Auswertung

Jede tatsächlich gespeicherte SVG-Ausgabe wird außerhalb der gemessenen Suche
erneut gerendert. Die unveränderten strengen Pixel-/Komplexitätsgrenzen aus
`tools/run_plan_b_variations.py` und die vorhandenen Ventil-/Textprüfungen
gelten gemeinsam. Bei Grundformen werden Komponentenanzahl, Außenboxen und
Positionen sowie Konturklassen geprüft. Die Konturprüfung akzeptiert auch
äquivalente SVG-Pfade. Eine kleine globale MSE allein genügt nicht.

Fehlende Ausgaben und sämtliche Fehlversuche bleiben im Nenner. Mittelwerte
der Pixelqualität nur vorhandener SVGs stehen ausdrücklich als bedingte
Ausgabemetriken im Bericht. Fehlende Objekte und fehlende Ausgaben werden
getrennt gezählt; ein Timeout ohne SVG erhält keinen erfundenen Pixelscore.
`runtime_satisfactory` wird getrennt von der unabhängigen Freigabe gespeichert.

`tools/anytime_observer.py` zählt Aufrufe des tatsächlichen Produktionsrenderers
im Worker, einschließlich Abschlussrendern. Beginn, Ende, Fehler und
unterbrochene Aufrufe bleiben in zeilenweise geschriebenen Telemetriedateien
erhalten. Renderaktivzeit wird hochauflösend gemessen. Das sind Renderaufrufe,
keine Vorschlagszahlen oder Cachezugriffe; die Offline-Auswertung zählt nicht
mit. Die Beobachtung hat Schreib-/Hashkosten und kann absolute Laufzeiten
leicht verändern. Beide Stände verwenden dieselbe Beobachtung.

## Ergebnisse

Die vollständige Matrix enthält **192 echte Bildversuche**, davon 185 mit
gespeicherter SVG. **113 Versuche bestehen** die unabhängigen Pixel- und
Strukturprüfungen gemeinsam. 72 vorhandene SVGs verfehlen beide Prüfarten;
sieben Versuche enden an der Ein-Sekunden-Grenze ohne gültige Ausgabe.
Kein unabhängig abgewiesenes Ergebnis ist als Runtime-Erfolg markiert.
Alle 377 Archivpaare bleiben unverändert. Bericht und wiederholbare Prüfungen:
`artifacts/evaluation/anytime_search_v1/report.json` und `checks.json`.

Je Zeile sind es acht Fälle mal drei Seeds. Renderzahlen umfassen alle
Versuche; Zeiten sind Bildzeiten einschließlich Workerstart, keine CLI-Gesamtzeiten.

| Stand | Budget | Bestanden | Median / p95 Bildzeit (s) | Median / p95 Renderaufrufe |
| --- | ---: | ---: | ---: | ---: |
| Elternstand | 1 s | 11/24 | 0,679 / 1,014 | 93,5 / 331,60 |
| Scheduler | 1 s | 12/24 | 0,719 / 1,000 | 93,5 / 267,50 |
| Elternstand | 5 s | 15/24 | 1,227 / 1,464 | 180 / 473,20 |
| Scheduler | 5 s | 15/24 | 1,031 / 1,469 | 158 / 260,00 |
| Elternstand | 15 s | 15/24 | 1,195 / 1,472 | 180 / 473,20 |
| Scheduler | 15 s | 15/24 | 1,094 / 1,420 | 165,5 / 251,05 |
| Elternstand | 60 s | 15/24 | 1,078 / 1,407 | 180 / 473,20 |
| Scheduler | 60 s | 15/24 | 1,094 / 1,601 | 165 / 310,15 |

An der Ein-Sekunden-Grenze gewinnt der Scheduler zwei gepaarte Versuche und
verliert einen; dies ist kein belastbarer allgemeiner Qualitätsgewinn.
Ab fünf Sekunden bestehen bei beiden Ständen jeweils dieselben fünf Fälle:
beide bekannten JPEGs, die erste Hz-Beschreibung und beide gemischten Szenen.
Die Hz-Umformulierung, Ellipse und Dreieck scheitern bei allen Seeds und allen
Budgets. Größere Suchbudgets beheben diese Struktur-/Dispatchfehler nicht.
Die Runtime beendet diese Fälle früh mit unzureichender Ausgabe, statt die
volle Minute auszuschöpfen. Insgesamt wurden 28.578 Renderaufrufe beobachtet;
ein Aufruf wurde bei einem Timeout unterbrochen.

Die Batchgesamtzeiten bleiben im Rohbericht erhalten. Ein Elternbatch mit
60-Sekunden-Grenze und Seed 42 benötigt auffällige 1.311,579 Sekunden, obwohl
seine acht gemessenen Bildzeiten zwischen 0,578 und 1,812 Sekunden liegen.
Diese Unterbrechung außerhalb der berichteten Bildarbeit wird nicht entfernt
oder den Optimierern zugerechnet. Aus den Bildzeitquantilen lässt sich deshalb
keine Garantie für die Gesamtdauer eines CLI-Aufrufs ableiten.
Eine separate Wiederholung derselben acht Fälle mit demselben Elternstand,
Seed und Budget benötigt 11,187 Sekunden und erzeugt acht bytegleiche SVGs.
Sie liegt unter `diagnostic_replay/`, ersetzt den Ausreißer nicht und zählt
nicht zur primären Matrix. Die Ursache der einmaligen Batchunterbrechung ist
damit nicht nachgewiesen; sie lässt sich in dieser Gegenprobe nicht wiederholen.

## Geltungsbereich und Folgerungen

Dies ist ein kleiner eingefrorener Windows-Vergleich mit drei Suchseeds,
keine allgemeine Optimiererrangliste. Unbekannte Familien sind hier synthetisch;
eine breite Abnahme unbekannter realer Katalogfamilien folgt daraus nicht.
Die frühe Erfolgsabschaltung bleibt aktiv. Größere Budgets versprechen deshalb
weder längere Suche noch eine stetige Verbesserung jeder Einzelmetrik.
Betriebssystemlast kann insbesondere die Ein-Sekunden-Grenze beeinflussen.

Der nachgewiesene Umformulierungsfehler und die beiden fehlgeschlagenen
Formfamilien liefern konkrete Kontrollfälle für GENERAL-SCENE-01. Weniger
Renderaufrufe bei einzelnen Kurztexten begründen noch keine Entfernung eines
Such-Bots; COMPONENT-VALUE-01 soll deren Beiträge einzeln und in Kombination
messen. Es bleibt das nächste dokumentierte Architekturpaket. Die offenen
Szenen- und Kompatibilitätsaufgaben bleiben erhalten.

Die 377 archivierten Bild-/SVG-Paare werden vor und nach dem Versuch vollständig
gegen ihre vorhandenen Hashes geprüft. Weder der Archivindex noch die Dateien
werden verändert. Das ist Bestandsschutz; eine erneute Produktionskonvertierung
aller 377 Bilder ist kein Teil dieses Messpakets.

## Reproduktion

Frische Ziel- und Arbeitsverzeichnisse verwenden. Der vollständige Bericht,
Quellraster, gespeicherte Ausgaben und Rohtelemetrie sind versioniert;
temporäre Elternmodule, Eingabekopien und vollständige CLI-Berichte bleiben
unter `.tmp/`.

```powershell
.venv/Scripts/python.exe -m tools.run_anytime_benchmark --output-dir .tmp/anytime-replay --work-dir .tmp/anytime-replay-work --baseline-ref 00d48fe5c
.venv/Scripts/python.exe -m tools.run_anytime_benchmark --verify-only --output-dir artifacts/evaluation/anytime_search_v1
.venv/Scripts/python.exe -m pytest tests/test_anytime_benchmark.py --basetemp .tmp/pytest-anytime
.venv/Scripts/python.exe -m compileall -q src tools tests
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

`--budgets 1 --seeds 17` ermöglicht eine kleine echte CLI-Gegenprobe. Dieser
reduzierte Lauf ersetzt die vollständige Abnahmematrix nicht. Die Verifikation
verlangt die vollständige im Bericht erklärte Matrix und weist fehlende oder
doppelte Zellen, geänderte Raster/SVGs/Telemetrie, falsche Workerquellen und
abweichende Qualitätsauswertungen zurück.

100 betroffene Tests bestehen, darunter 13 neue Benchmarkregressionen und
87 vorhandene Steuerungs-, Prozess- und Kurztexttests. Sie prüfen unter anderem
fehlende/duplizierte Messzellen, unveränderte Nenner bei Timeouts, manipulierte
Quellen/Ausgaben, eine kleine fehlende Form trotz niedriger globaler MSE,
Formklassen trotz gleicher Außenbox und die Gleichheit der Umformulierungsraster.
Syntaxprüfung und das Verbot von Bild-ID-Hardcoding bestehen ebenfalls.
Ein vollständiger Repository-Testlauf wurde nicht durchgeführt.
