# COMPONENT-VALUE-01 – tatsächlicher Beitrag der sechs Such-Bots

Arbeitsbranch: `codex/component-value-01-2026-10-18`.

## Runtime und Schalter

`imageCompositeConverterComponents.py` registriert zunächst die sechs produktiven
Parameter-Bots mit Kennung, Version, Voraussetzungen und CLI-Schalter.
`--disable-search-bot NAME` ist wiederholbar und wird bis in den überwachten
Spawn-Worker übernommen. Unbekannte Namen sowie Kombinationen mit `legacy` oder
`fixed` werden abgewiesen. Die Qualitätsprüfungen stehen nicht zur Abschaltung.
Ohne diesen Schalter bleibt das bisherige Portfolio aktiv.

Abgeschaltete Bots werden nicht initialisiert, erhalten keine Suchabschnitte
und erzeugen keine Vorschläge. Ein Konstruktor- und Vorschlagswächter prüft
dies für jede Einzelabschaltung sowie das vollständig abgeschaltete Portfolio.
Das gemeinsame Zeit-/Vorschlagsbudget bleibt gleich; andere Bots dürfen die
verbleibende Arbeit übernehmen. Das Stagnationsfenster je Bot bleibt unverändert.
Die Abschaltmaske gehört zur Blackboard-Kennung, damit eine andere Konfiguration
keinen alten Suchzustand übernimmt. Generatoren und Zufallszahlen bleiben
gekoppelt: Das Entfernen eines Bots kann auch die späteren Vorschläge seiner
Kollegen verändern. Gemessen wird deshalb der Beitrag zum gesamten Portfolio,
nicht ein isolierter, additiver Einzelbeitrag.

Je Bild enthält `reports/<name>_components.jsonl` die tatsächlich im Worker
beobachteten Schalter und einen Abschlussstand. Detailzähler unterscheiden
erzeugte Vorschläge, gemeinsam vermiedene Wiederholungen, zulässige/abgewiesene
Messungen, übernommene Verbesserungen und aktive Messzeit. Cachetreffer gehören
dem anfragenden Bot; gemeinsame Vorarbeiten und Rendering außerhalb der
Botsuche werden nicht einem Sieger zugeschlagen. Eine Verbesserung des
Suchverlusts ist keine unabhängige Qualitätsfreigabe.

Die Zähler kosten konstanten Aufwand je Vorschlag; es gibt zwei zusätzliche
Zusammenfassungsschreibvorgänge je Worker und keine neue Datei je Vorschlag.
`--no-component-observation` schaltet die zusätzlichen Detailzähler ab.
Die bereits vorhandenen Vorschlagszähler und der Konfigurationsnachweis bleiben
erhalten. `observation_seconds` misst eng die zeitlich umschlossenen
Zähleraktualisierungen, nicht sämtliche Diagnose-/Dateikosten. Der gepaarte
`unobserved`-Arm misst die Wirkung dieser Detailbeobachtung auf die gesamte
Bildarbeit. Renderbeobachtung und Grunddiagnostik sind in beiden Armen aktiv.
Spitzen-RSS wird im zuletzt protokollierten Worker einschließlich Imports und
nativer Bibliotheken erfasst. Frühere Retry-Worker sind darin nicht vollständig
enthalten; das ist keine Spitze des gesamten Prozessbaums. Renderer-Kindprozesse
sind in diesem Vergleich deaktiviert.

Bei einem hart beendeten Worker ohne Abschlussereignis sind die Arbeitszähler
unvollständig. Der Bericht weist solche Beobachtungen gesondert aus; fehlende
Messwerte sind kein Nachweis fehlender Arbeit. Auch ein regulär abgeschlossener
Versuch ohne Ergebniszeile erhält jetzt einen Zeit-/Aufsichtsnachweis.

## Gepaarter Produktionsvergleich

`python -m tools.run_component_value` verwendet die echte überwachte
`semantic-only`-CLI. Jeder Arm/Seed erhält frische Rasterkopien, Ausgaben und
Caches. Suchhistorie und Referenz-SVGs werden nicht als Eingaben verwendet.
Quellhashes, Beschreibungen, Rasterhashes, Plattform, Seeds, Schalterzustände,
Bild-/Batchzeit, SVGs, Rendererereignisse und Komponentenbeobachtung bleiben
im Bericht beziehungsweise den Rohartefakten erhalten. Hinzu kommen die
tatsächlichen Registrierer, ihre Suchgewinner und gegebenenfalls Checkpoint-
Nachweise aus dem nativen Konvertierungsbericht. Die Reihenfolge der
Arme rotiert und kehrt sich zwischen Seeds um. Konvertierungen laufen seriell.
Der vollständige Repository-Testlauf lief parallel zur endgültigen lokalen
Messreihe. Diese zusätzliche Rechnerlast begrenzt die Interpretierbarkeit der
Zeitunterschiede; daraus wird keine Leistungsoptimierung abgeleitet.

Das produktive Bot-Budget beträgt fünf Sekunden einschließlich Workerstart und Abschluss,
mit derselben harten Grenze ohne Verlängerung. Die Seeds sind 17, 42 und
20261018. Verglichen werden das vollständige Portfolio, jede der sechs
Einzelabschaltungen, die gemeinsame Abschaltung von `joint_restart` und
`geometry_pair`, alle Bots aus, Geometrie allein, Geometrie plus Neustarts und
der Arm ohne Detailzähler. Der Wiederaufbau ist eine vorab begrenzte Auswahl
von Wechselwirkungen, keine vollständige Untersuchung aller 64 Teilmengen.

Die Entwicklungsfälle umfassen echte Ventil-, rF- und Lux-Raster sowie eine
gemischte Grundformszene. Der erste getrennte Prüfbestand enthält neue
Hz-Beschreibungen mit identischen Quellpixeln, eine weitere Anordnung,
Ellipse und Dreieck. Die Hz-Umformulierung und beide unbekannten Formfamilien
bleiben absichtlich im Nenner. Ein Fall ohne gespeicherte SVG ist ein Fehler;
seine Pixelqualität wird nicht erfunden.

Jede vorhandene SVG wird anschließend unabhängig erneut gerendert und gegen
die unveränderten strengen Pixel-/Komplexitätsgrenzen sowie Objektzahl,
Positionen, Formklassen beziehungsweise Text-/Ventilstruktur geprüft.
`runtime_satisfactory` bleibt von dieser Freigabe getrennt. Die Verifikation
weist fehlende/doppelte Messzellen, geänderte Quellen, Ausgaben, Telemetrie,
Budgets, Schalter oder falsche Workerquellen zurück.

## Kontrollfälle und Entscheidung

Vier ausdrücklich künstliche Kontrollarme prüfen den Nachweisrahmen auf zwei
echten Raster-/Beschreibungsfällen. Zwei austauschbare Renderer-Zugänge rufen
denselben Produktionsrenderer auf. Einer allein muss dieselben SVGs liefern;
beide aus müssen die Konvertierung scheitern lassen. Diese Kontrollen verwenden
den bestehenden festen Suchablauf mit Vorschlagsbasis 32 und für alle vier
Arme dieselben 15 Sekunden Bildbudget. Ein weiterer Arm wartet
einmal vor dem ersten Renderaufruf jedes Workers zusätzlich zwei Sekunden
(bei Wiederholungs-Workern erneut) und muss dieselben SVGs mit
höherem Aufwand erzeugen. Diese Eingriffe verändern weder Quellraster noch
Qualitätsgates. Sie sind keine zusätzlichen produktiven Erkennungsverfahren
und begründen keine Aussage über die Nützlichkeit eines Such-Bots.

Der erste Kontrollversuch verwendete wie die produktiven Arme adaptive
Zeitscheiben und fünf Sekunden. Er verfehlte die verlangte Bytegleichheit:
alle Renderer-Varianten lieferten akzeptierte Ergebnisse, aber die zusätzlichen
Wartezeiten verschoben die Szenenauswahl des Schedulers. Diese 24 tatsächlichen
Versuche bleiben unter `artifacts/evaluation/component_control_timing_probe_v1`
mit den abgewiesenen Kontrollkriterien erhalten. Sie zählen nicht als bestandene
Kontrollabnahme. Erst danach wurden die Kontrollen auf den festen Ablauf mit
gleichem größerem Budget umgestellt und vollständig neu ausgeführt. Die 324
produktiven Bot-Gegenproben und alle Qualitätsgrenzen wurden dabei erhalten.
Auch der feste Versuch mit wiederholter Verzögerung pro Renderaufruf bleibt
unter `component_control_render_delay_v1` erhalten: Die Rundung sehr kurzer
Windows-Wartezeiten führte dort zu drei Zeitabbrüchen ohne gültige Ausgabe.
Diese unzureichende Kontrolle wurde durch die einmalige Verzögerung je Worker
ersetzt; die bereits nachgewiesenen festen Renderer-Alternativen blieben erhalten.

Die produktive Einstufung unterscheidet Nutzen, Schaden, Gleichwertigkeit im
untersuchten Bereich und unklare Evidenz. Vorab festgelegt sind mindestens
acht unabhängige Familien, fünf Prozentpunkte Akzeptanz-Gleichwertigkeit,
zehn Prozent Laufzeit und ein Prozent relative Ausgabe-MSE. Die konservative
95-Prozent-Hoeffding-Grenze wird über Familien berechnet; Seeds und
Umformulierungen vermehren deren Anzahl nicht. Ein fehlender signifikanter
Unterschied wird nicht als Gleichwertigkeit ausgegeben. Die MSE- und
Zeitvergleiche allein dürfen keine fehlende Ausgabe oder ein fehlendes Objekt
überdecken.

Die konkrete geprüfte Entscheidung ist die **Beibehaltung aller sechs Bots**.
Als Gegenkandidaten dienen die Entfernung der Feinregistrierung sowie die
Entfernung des ganzen zusätzlichen Bot-Portfolios. Der ergänzende, vor seinen
Läufen eingefrorene Abnahmebestand verwendet neue kWh-, mPa- und dB-Symbole
mit anderen Größen, Farben und Zeichenabständen. Daran werden diese beiden
Vereinfachungen erneut gegen das unveränderte Portfolio geprüft. Dieser
Bestand wird weder zur Gewichtsanpassung noch zum Training verwendet.

Der kleine Bestand kann keine allgemeine Entbehrlichkeit nachweisen. Seltene
Fähigkeiten, Abhängigkeiten anderer Erkenner und Schutz-/Wiederherstellungspfade
sind weiterhin Gründe gegen eine automatische Entfernung. Die bestehende
Scheduler-Zuteilung wird aus diesen Abnahmedaten nicht nachtrainiert.

## Wiederholung und CI

### Lokale Ergebnisse (Abschluss am 19. Oktober)

Die definitive Hauptmatrix enthält 348 Versuche mit 343 gespeicherten SVGs und 230
unabhängigen Freigaben. Davon sind 324 produktive Bot-Gegenproben und 24
abschließende Kontrollen. Fünf produktive Versuche enden ohne gültige Ausgabe;
sie bleiben im Nenner. Einer davon endet bereits vor der Schalterbeobachtung.
Er gilt als unbeobachtet und kann keinen positiven Schalternachweis liefern.
Die beobachteten abgeschalteten Bots erzeugen keine Vorschläge; zusätzlich
prüfen Konstruktor- und Vorschlagswächter die vollständige Abschaltung.

| Produktive Konfiguration | Entwicklung | Getrennter erster Prüfbestand |
| --- | ---: | ---: |
| Vollständiges Portfolio | 12/12 | 6/15 |
| Ohne Feinregistrierung | 11/12 | 6/15 |
| Ohne gemeinsame Neustarts | 11/12 | 6/15 |
| Nur Geometrie | 11/12 | 6/15 |
| Nur Geometrie plus Neustarts | 11/12 | 6/15 |
| Ohne alle Bots | 12/12 | 6/15 |

Die übrigen sechs produktiven Varianten bestehen wie das vollständige Portfolio
18/27 Fälle. Die vier beobachteten Verluste sind Zeitabbrüche beim Lux-Fall,
keine belastbare allgemeine Rangfolge. Alle produktiven Einstufungen bleiben
unklar. Der anschließende neue Abnahmebestand besteht 27/27 in allen drei
Konfigurationen. Dort erzeugt kein Bot Vorschläge: Der Bestand bestätigt die
Beibehaltung ohne neue Regression, prüft aber keine seltene Bot-Fähigkeit positiv.
Eine dauerhafte Vereinfachung ist aus diesen Daten nicht begründet.

Die abschließenden Renderer-Kontrollen bestehen ihre Identitätskriterien über
alle sechs Paarungen. Der Zusatzaufwand erhöht die gemessene Zeit, beide
abgeschalteten Zugänge verhindern jede vollständige Freigabe. Alle 377
Archivpaare bleiben gegen ihre vorhandenen Hashes unverändert. Unterbrochene
CLI-Batches bleiben in den Rohdaten; das Maximum der definitiven Matrix
beträgt 22.587,672 Sekunden. Die Ursache ist nicht nachgewiesen; Bildzeit und Batchzeit bleiben
getrennt und begründen keine Garantie für die CLI-Gesamtdauer.

Die Ergebnisse und Grenzen stehen zusätzlich in den README-Dateien und kompakten
`summary.json` der versionierten Ordner `component_value_v1` und
`component_retention_v1`. Zusammen mit Manifest und Prüfzahlen bleiben diese im
Repository. Generierte Raster, SVGs, Rohereignisse, vollständige Berichte und
Testlogs sowie die Voruntersuchungen und gescheiterten Kontrollentwürfe bleiben
lokal erhalten und werden von Git ignoriert. CI-Läufe laden ihre eigenen
vollständigen Nachweise als Workflow-Artefakte hoch. Die weitergehende Untersuchung seltener
realer Familien und weiterer Komponenten bleibt Folgearbeit. Der nächste
geplante Architekturversuch ist NEURAL-ELEMENTS-01; eine Netzübernahme setzt
weiterhin einen unabhängigen realen End-to-End-Nutzen voraus.

Die Voruntersuchung mit abgeschalteten Vorschlägen, aber noch gemeinsam
angelegten Bot-Startobjekten bleibt unter `component_activation_probe_v1`
einschließlich damaliger Suchmodulquelle erhalten. Nach dem korrigierten
Schaltpunkt wurde die gesamte definitive Matrix mit unveränderten Gates neu
ausgeführt; auch der getrennte Abnahmebestand wurde wiederholt.

Ein Reporterfehler wurde durch Auslesen bereits abgeschlossener nativer
Konvertierungen behoben. Für diese neun Einträge fehlen CLI-Batchdauer und
Exitcode; sie bleiben ausdrücklich `null`. Die tatsächlich gemessenen Bildzeiten
und erzeugten Ausgaben werden nicht durch einen neuen Versuch ersetzt.

### Befehle

Frische Ziel- und Arbeitsordner verwenden:

```powershell
.venv/Scripts/python.exe -m tools.run_component_value --output-dir .tmp/component-study --work-dir .tmp/component-study-work
.venv/Scripts/python.exe -m tools.run_component_value --suite retention --output-dir .tmp/component-retention --work-dir .tmp/component-retention-work
.venv/Scripts/python.exe -m tools.run_component_value --verify-only --output-dir .tmp/component-study
.venv/Scripts/python.exe -m tools.run_component_value --verify-only --output-dir .tmp/component-retention
.venv/Scripts/python.exe -m pytest tests/test_component_value.py
```

Die ursprünglichen lokalen Messungen können weiterhin mit `--verify-only` und
ihrem jeweiligen Ordner unter `artifacts/evaluation` geprüft werden. Das setzt
die dort erhaltenen, ignorierten Rohdaten voraus. Nach einem frischen Checkout
zuerst mit den obigen Befehlen eigene Messungen erzeugen.

`--smoke --seeds 17` prüft nur zwei Fälle und drei Arme und ersetzt die
Abnahme nicht. Der neue CI-Job `component-value` führt regelmäßig die echte
vollständige Variantenmatrix einschließlich Kontrollen mit einem Seed aus,
verifiziert die Ausgaben erneut und lädt die Belege hoch. Ein einzelner
CI-Seed ist eine technische Regression, kein Ersatz für drei Suchseeds und
einen getrennten Abnahmebestand. Erkennung und Nachbearbeitung können später
eigene Registry-Einträge erhalten; dieses erste Paket untersucht die sechs
Bots. IDO-19/IDO-21 werden dadurch nicht pauschal geschlossen.

`--resume` prüft bereits gespeicherte Messzellen unabhängig erneut und setzt
einen unterbrochenen Lauf mit unveränderten Runtime-Quellen und Einstellungen
fort. Ein rotierter Vergleichsarm ohne seine noch nicht ausgeführte Referenz
bleibt vorläufig ungepaart; die Abschlussprüfung verlangt weiterhin die ganze
Matrix. Diese Unterscheidung ist durch einen Regressionstest abgesichert.

### Abschlussprüfungen

Der vollständige Standard-Testlauf besteht mit **3.526 bestandenen und 30 nach
Repository-Voreinstellung übersprungenen Tests**. Der Lauf begann vor den
abschließenden Regressionsergänzungen. Gegen den finalen Stand bestehen zusätzlich
alle **147 betroffenen Tests**, einschließlich Konstruktorabschaltung,
Wiederaufnahme, unbeobachtetem Startabbruch, Prozessaufsicht und Herkunftsschutz.
Log und JUnit-Nachweis liegen lokal unter `component_value_v1/validation`;
ihre kompakten Prüfzahlen stehen in der versionierten `summary.json`.

Syntaxprüfung von `src`, `tools` und `tests`, CLI-Hilfe, das Verbot von
Bild-ID-Hardcoding und der Whitespace-Check bestehen. Beide definitiven
Messmatrizen werden unabhängig erneut geprüft. Der neue GitHub-Job ist
verdrahtet; ein entfernter CI-Lauf wurde hier nicht gestartet. Die sehr langen
Unterbrechungen bleiben auch im Standard-Testlog erhalten und begründen keine
Aussage über typische Test- oder Konvertierungsgeschwindigkeit.
