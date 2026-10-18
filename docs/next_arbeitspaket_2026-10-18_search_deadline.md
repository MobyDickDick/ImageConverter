# Arbeitspaket – überwachte Bildbudgets und geprüfte Zwischenstände

Ausgangsstand: `2c7694cd2`. Nach AC0232 war SEARCH-DEADLINE-01 als nächste
Architekturaufgabe dokumentiert.

## Produktionspfad

Die reguläre `semantic-only`-CLI überwacht jetzt jeden Bildversuch in einem
eigenen Prozess. Die Bildzeit umfasst Prozessstart, Bildvorbereitung, alle
Optimierer, semantische Prüfungen, abschließende Qualitätsmessungen und die
Erzeugung der PNG-Vorschau. Auch ältere, nicht an die kooperative Suchuhr
angeschlossene Optimierer liegen innerhalb dieser Grenze.

Das normale Budget beträgt weiter 60 Sekunden. Ein tatsächlich gemessener
deutlicher Fortschritt kurz vor der Grenze erlaubt dieselben begrenzten
15-Sekunden-Verlängerungen bis höchstens 120 Sekunden. Eine Verbesserung
erlaubt höchstens eine Verlängerung; ein blockierter Aufruf allein kauft keine
Zeit. `ICC_CONVERSION_TIMEOUT_SEC` setzt gegebenenfalls eine engere Grenze.
Andere Bilder verbrauchen dieses Budget nicht. Wiederholungen desselben Bildes
erhalten weder eine neue Uhr noch neue Suchhistorie.

Der Hauptprozess überwacht mit kurzen Warteabschnitten. Unter Windows hält
ein Jobobjekt den Worker und seine nativen Renderkinder zusammen; unter Unix
verwendet der Worker eine eigene Prozessgruppe. Die Eindämmung muss vor dem
Beginn der Konvertierung gelingen. An der Grenze werden auch Renderkinder
beendet. Betriebssystemplanung, Prozessbereinigung und das Schreiben der
Batchberichte benötigen zusätzlich Zeit: Die 60/120 Sekunden sind die Grenze
für die Bildbearbeitung, keine millisekundengenaue Gesamtlaufzeitgarantie für
einen CLI-Aufruf.

## Sichere Ergebnisübergabe

Jeder Versuch schreibt zunächst in einen eigenen temporären Ausgabebereich.
Der Hauptprozess übernimmt eine abgeschlossene Übergabe erst, wenn auch die
abschließenden Messungen und die Vorschau vorliegen. Ein beendeter Worker
kann keine halb geschriebene SVG-Ausgabe veröffentlichen.

Die vorhandenen Modellprüfungen können zusätzlich einen Zwischenstand melden,
nachdem die lokale Semantik und alle unveränderten strengen Pixelgrenzen
bestanden sind. Der Worker bindet ihn an das tatsächlich geladene Quellraster,
den Quelldateihash und den SVG-Hash. Die Messwerte und PNG-Pixel werden vor der
Übergabe erzeugt. Nach einem Abbruch ist deshalb kein neuer Renderaufruf nötig.
Bei mehreren gültigen Zwischenständen entscheidet der vorhandene räumliche
Qualitätsscore. Beschädigte Übergaben und geänderte Quellen werden abgewiesen.

Ein bereits vollständig gemessenes Ergebnis desselben Laufs bleibt bei einer
abgebrochenen Wiederholung erhalten. Ein unzureichendes Ergebnis wird dadurch
nicht zum Erfolg. Ohne geprüften Zwischenstand entsteht ein dokumentierter
Fehler statt einer Erfolgsplatzhaltergrafik. Zwischenstände werden nur innerhalb
dieses Aufrufs verwendet; frühere Ausgaben und Archiv-SVGs werden nicht als
Konvertierungsquellen geladen. Auch der neue Worker selbst sperrt fremde
SVG-Lesezugriffe und berichtet blockierte Zugriffe.

Die nachgelagerten Rankings und Übersichten verwenden die bereits im Worker
gemessenen Zeilen und erzeugten PNGs. Sie starten keinen weiteren SVG-Renderer.
Die historische größenübergreifende Harmonisierung und die Rückübernahme alter
Erfolgssnapshots verändern die ausgewählte Ausgabe in diesem Pfad nicht mehr.
Damit bleiben die Modellprüfung, der gespeicherte SVG und seine Messwerte
zusammengehörig.

## Bedienung und Geltungsbereich

```powershell
.venv/Scripts/python.exe -m src.imageCompositeConverter EINGABE --descriptions-path BESCHREIBUNGEN.xml --output-dir AUSGABE --start ERSTES --end LETZTES --search-seconds 60 --search-max-seconds 120 --search-seed 42
```

`--isolate-conversion` ist für `semantic-only` voreingestellt. Auch
`--search-mode legacy` und `--search-policy fixed` bleiben in diesem Pfad
überwacht; ohne Fortschrittsmeldungen gibt es keine adaptive Verlängerung.
`--no-isolate-conversion` ermöglicht den bisherigen direkten Ablauf für
gezielte Entwicklungsvergleiche. Dieser ausdrücklich gewählte Ablauf hat
keine neue harte Prozessgarantie.

Der historische `--execution-mode standard` behält seine vorhandenen
Wiederverwendungs-, Transfer- und Harmonisierungspfade. Seine vollständige
Prozessaufsicht ist als SEARCH-DEADLINE-COMPAT separat offen; der vorliegende
Abschluss und die Zeitgarantie gelten für den regulären `semantic-only`-Pfad.
Auch die reine Kompatibilitäts-API `convert_image` aktiviert diese CLI-Policy
nicht selbstständig.

`search_control.isolated` und `reports/deadline_policy.json` dokumentieren die
Policy. Bei einem Abbruch enthält `reports/*_deadline.json` Budget, verbrauchte
Bildzeit, Abbruchgrund und den Status der erhaltenen Ausgabe. Eine gerettete
Zeile enthält zusätzlich `checkpoint_proof`. Workerlogs bleiben auch bei
einem Timeout erhalten.

## Nachweise

Unter `artifacts/evaluation/deadline_search_v1/` liegen geschützte neutrale
Quellen, tatsächliche direkte und überwachte CLI-Ausgaben und unabhängige
erneute Messungen. Acht Fälle umfassen drei Ventilgrößen, eine Q-Scheibe mit
Griff, zwei Kurztexte und zwei unabhängige Grundformanordnungen. Alle acht
überwachten SVGs sind zu ihrem direkten Kontrolllauf bytegleich. Beide
Ausgaben jedes Falls bestehen die unveränderten strengen Pixelgrenzen und
die unabhängige jeweilige Objekt-/Textprüfung.

Eine weitere Fehlerprobe verwendet den echten Ventilfit: Erst nachdem seine
Semantik und die strengen Pixelgrenzen bestanden sind, wird der nächste
Renderer absichtlich blockiert. Nach vier Sekunden beendet die Aufsicht den
Worker und rettet das geprüfte SVG. Die unabhängige erneute Render- und
Objektprüfung besteht. Dies ist ein tatsächlicher Prozessabbruch mit einem
echten Konvertierungsergebnis; die kurze Vier-Sekunden-Grenze ist ausdrücklich
eine Testkonfiguration.

15 zusätzliche Spawn-/Runtime-Tests prüfen unter anderem blockierte erste Berechnungen,
unvollständige Übergaben, falsche SVG-/Quellhashes, verfehlte Gates,
Bildwechsel, Abstürze, geteilte Wiederholungsbudgets, spätes Fortschreiten,
engere externe Grenzen und das Beenden eines tatsächlich gestarteten
Kindprozesses. Eine echte CLI-Regression verbietet jeden SVG-Renderer im
Hauptprozess und prüft trotzdem die Ausgabe und die Übersicht. Eine weitere
Gegenprobe erzwingt einen fremden SVG-Leseversuch im tatsächlichen Worker:
Der Zugriff wird gesperrt und auch bei fehlgeschlagener Konvertierung berichtet.

Die erneute echte CLI-Konvertierung aller **377 Archivpaare** besteht die
unveränderte absolute Archiv-Pixelgrenze. Dazu gehören 329 `semantic-only`-
und 48 historische `standard`-Fälle. Alle **377 gespeicherten neuen SVGs**
sind bytegleich zu einem zusätzlichen frischen direkten CLI-Kontrolllauf.
Originalbilder, gespeicherte Bestresultate und sämtliche 377 Archivdatensätze
bleiben anhand ihrer Hashes unverändert. Die absolute Archivgrenze ersetzt
keine der strengeren Paketprüfungen. Ausgaben, Kontrollhashes und Workerlogs
sind im Nachweisordner erhalten.

Das frisch gesammelte Defaultprofil umfasst **3.508 Testknoten**: **3.478
bestanden, 30 regulär übersprungen, null Fehler**. Vier getrennte Prozesse
prüfen die Suite; der abschließende 15-Fälle-Lauf ersetzt in der Auswertung
die frühere Fassung dieses Testmoduls. Die Zusammenführung weist jeden frisch
gesammelten Testknoten exakt einmal nach. Die zusätzlichen AC08-/AC0100-Smokes
bestehen ebenfalls (2/2). `compileall`, CLI-Hilfe, Hardcoding-Nullprüfung und
`git diff --check` bestehen.

## Reproduktion

```powershell
.venv/Scripts/python.exe -m tools.run_deadline_evidence --verify-only --output-dir artifacts/evaluation/deadline_search_v1
.venv/Scripts/python.exe artifacts/evaluation/deadline_search_v1/seal_evidence.py --verify
.venv/Scripts/python.exe -m tools.run_deadline_evidence --output-dir .tmp/deadline-replay
.venv/Scripts/python.exe -m pytest tests/test_conversion_deadline.py --basetemp .tmp/deadline-tests
.venv/Scripts/python.exe artifacts/evaluation/deadline_search_v1/run_checks.py
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --max-cases-per-worker 50 --output-dir .tmp/deadline-archive-replay
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --max-cases-per-worker 50 --no-isolate-conversion --output-dir .tmp/deadline-archive-direct-replay
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

Die Tests des vollständigen Defaultprofils verwenden für Modellprüfungen den
direkten Renderer (`IMAGE_CONVERTER_ISOLATE_SVG_RENDER=0`); die ausdrücklichen
Render- und Prozessisolationstests bleiben enthalten. Es werden keine
Qualitätsgrenzen gelockert. Die beiden Sucharchitekturaufgaben
SEARCH-SCHEDULER-02 und BENCHMARK-ANYTIME-01 bleiben offen.
