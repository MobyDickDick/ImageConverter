# SEARCH-SCHEDULER-02 – gemeinsame Modellzeitscheiben

Arbeitsbranch: `codex/search-scheduler-02-2026-10-18`.
Ausgangsstand: `00d48fe5c`, der die vorgefundenen uncommitteten Änderungen von
SEARCH-DEADLINE-01 separat sichert. `main` bleibt auf `2c7694cd2`; der identische
lokale Branchverweis `AddTimeSlot` wurde entfernt. Auf dem Remote existierte
bereits nur `main`.

## Umsetzung

Registrierungen sind jetzt als fortsetzbare Generatoren ausführbar. Die
bisherige synchrone Schnittstelle führt dieselben Schritte bis zum Ergebnis
aus. Ein gemeinsamer Scheduler vergleicht mehrere Modellgeneratoren in
Abschnitten mit höchstens acht Schritten oder 50 Millisekunden aktiver Zeit.
Ein bereits laufender Renderaufruf einschließlich seiner Qualitätsprüfung
kann diesen kooperativen Abschnitt überschreiten; die unveränderte äußere
Prozessaufsicht erzwingt weiterhin das Bildbudget.

Die Kurztext-Rekonstruktion verwendet diesen Ablauf tatsächlich für native
und getrennt positionierte Zeichen in beiden bisherigen Schriftgewichten.
Auch die anschließenden Zeichenverfeinerungen teilen sich Zeitscheiben.
Jeder Generator besitzt eigene Parameter, Gültigkeitsregeln und Zielfunktion.
Der gemeinsame Bildkontext startet seine Uhr bei einem Modellwechsel nicht neu.
Eine vollständige lokale Text-/Objektprüfung und die unveränderten strengen
Pixelgrenzen entscheiden weiterhin über Erfolg und die gesicherte Übergabe.
Die Priorität des Schedulers allein erlaubt keine Ausgabe.

Die sechs bestehenden Parameter-Bots verwenden dieselbe Verteilungsregel:
Zuerst bekommt jede aktive Alternative einen Abschnitt. Danach wird die
relative Verbesserung des zulässigen Suchverlusts durch die tatsächlich beanspruchte aktive Zeit
geteilt; der geglättete Wert bestimmt weitere Anteile. Warten auf andere
Modellgeneratoren zählt dabei nicht zur eigenen Rechenzeit. Nach ausreichend
vielen anderen Abschnitten erhält die am längsten wartende Alternative
erneut Zeit. Ein frühes Plateau schließt einen später hilfreichen gekoppelten
oder globaleren Start deshalb nicht aus. Die bestehende individuelle
Stagnationsabschaltung und die Vorschlags-/Verlängerungsgrenzen bleiben erhalten.

Ein bildgebundener Cache hält höchstens 256 registrierte SVG-Raster, auch
fehlgeschlagene Renderaufrufe. Verschiedene Modelle können damit identische
SVG-Vorschläge innerhalb dieses Fensters ohne erneutes Rendern prüfen.
Fehler und Suchverlust werden mit der jeweiligen aktuellen Zielfunktion neu
berechnet; semantische Freigaben werden nicht aus diesem Cache übernommen.
Das Bot-Blackboard behält zusätzlich seine bisherigen positiven und negativen
Parameterversuche. Nichts davon wird als Vorlage aus früheren Läufen geladen.
Der kompakte Schedulerzustand und der Cache sind mit der Workerübergabe
serialisierbar; laufende Generatoren werden darin nicht gespeichert.

`model_slice`, `model_schedule_finished`, `model_schedules` im Modellergebnis
und die Bot-Berichte dokumentieren Abschnitte, aktive Zeiten und Prioritäten.
Bei früher Annahme, Zeitende oder einem Fehler werden suspendierte Generatoren
geschlossen. Reihenfolgeabhängige Nachverfeinerungen beginnen mit der besser
gemessenen Hypothese.

## Geltungsbereich und verbleibende Aufgaben

Die gemeinsame Modellschnittstelle ist wiederverwendbar; der konkrete
mehrmodellfähige Runtime-Anschluss umfasst die beschriebenen Kurztextmodelle.
Andere Spezialpfade behalten ihre bisherigen Aufrufketten und die gemeinsame
Bilddeadline. Die zusätzliche Parametersuche dieser Registrierer nutzt bereits
die neue Bot-Verteilung. Neue Formen, zusätzliche Anschlüsse oder beliebige
Add/Remove/Replace-Operatoren sind weiterhin GENERAL-SCENE-01.

Die adaptive Reihenfolge hängt vom Seed **und** den gemessenen Kosten ab.
Betriebssystemlast kann daher den Pfad und das erste ausreichende Ergebnis
ändern. Regressionen mit injizierter Uhr prüfen die Wiederholbarkeit bei
gleichen Kosten. `--search-policy fixed` behält den zeitunabhängigen festen
Vergleichsablauf. Die harte Prozessgrenze gilt weiterhin für die reguläre
`semantic-only`-CLI; SEARCH-DEADLINE-COMPAT bleibt offen.

Der Elternvergleich belegt gültige Ausgaben und die tatsächliche Nutzung der
Zeitscheiben. Er zeigt keinen allgemeinen Geschwindigkeitsgewinn. Manche
Fälle kosten durch die zusätzliche Erkundung mehr Zeit. Auch einzelne
Pixelmetriken können sich innerhalb der unveränderten Gates verschieben;
ein früher ausreichender Fit ist keine Zusage einer überall optimalen Metrik.
Es werden keine neuen Optimierer aufgrund dieses kleinen Vergleichs als
allgemein überlegen eingestuft. Das nächste Paket ist BENCHMARK-ANYTIME-01:
Qualitätskurven, mehrere Seeds, weitere unbekannte Familien, Renderzahlen
sowie Median/p95 unter gleichen Zeitbudgets.

## Nachweise und Reproduktion

Der Nachweis liegt unter `artifacts/evaluation/scheduler_search_v1/`.
Elf neutrale Raster werden durch die echte überwachte CLI sowohl mit den
vier eingefrorenen Elternmodulen als auch mit dem neuen Scheduler konvertiert.
Ein temporärer Python-Paketoverlay wählt im Elternlauf die Quelltexte aus Git,
einschließlich der Windows-Spawn-Worker. Beide Läufe erhalten dieselben
Beschreibungen, Seeds und 60/120-Sekunden-Grenzen. Quellen und Modulstände sind
über SHA-256 gebunden. Die Runtime darf keine Referenz-SVGs lesen.

Die Fälle umfassen drei Ventilgrößen, eine Buchstabenscheibe mit Griff, zwei
Kurztexte, zwei Grundformszenen und drei neue Beschriftungs-/Geometriefälle.
Die Ausgabeprüfung rendert die gespeicherten SVGs unabhängig erneut und
prüft die strengen Pixelgrenzen sowie die jeweilige Text-/Objektstruktur.
Ergebnisse und Testzähler stehen in `report.json` und `checks.json`.

Alle 22 gespeicherten SVGs bestehen die unabhängigen Pixel-/Semantikprüfungen;
zehn der elf neuen Ausgaben sind zum Elternlauf bytegleich. Der veränderte
Kurztextfit besteht ebenfalls alle Gates, bei anderer Verteilung der
Einzelmetriken. 95 betroffene Runtime-Tests und der abschließende Lauf mit
87 Steuerungs-, Prozess- und Kurztexttests bestehen. Nach Zusammenführung der
überlappenden Fälle sind das **165 unterschiedliche bestandene Tests**.

Die Steuerungstests prüfen insbesondere faire Erkundung, Fortschritt pro
aktiver Sekunde, getrennte Zielfunktionen, gemeinsam verbrauchte Zeit,
Schließen suspendierter Modelle, erhaltene negative Versuche, aktuelle
Semantik trotz Cachetreffern und serialisierbaren Zustand. Eine echte
Registrierung mit injizierten Renderkosten zeigt, dass eine zweite Hypothese
rechtzeitig Erfolg erreicht, obwohl der erste stagnierende Fit alleine das
Budget verbrauchen würde. Die Prozessregressionen prüfen weiterhin blockierte
Worker, Kindprozesse und gerettete geprüfte Zwischenstände.

Die archivierten 377 Original-/SVG-Paare werden in diesem Paket per Hash
gegen den bestehenden Index geprüft. Eine vollständige erneute Konvertierung
des Archivs und ein vollständiger Repository-Testlauf sind hier nicht erfolgt.

```powershell
.venv/Scripts/python.exe -m tools.run_scheduler_evidence --output-dir .tmp/scheduler-replay --baseline-ref 00d48fe5c
.venv/Scripts/python.exe -m tools.run_scheduler_evidence --verify-only --output-dir artifacts/evaluation/scheduler_search_v1
.venv/Scripts/python.exe -m pytest tests/test_conversion_search_scheduler.py tests/test_adaptive_conversion_search.py tests/test_conversion_search_bots.py tests/test_search_portfolio.py tests/test_conversion_deadline.py tests/test_short_label_disk_runtime.py
.venv/Scripts/python.exe -m pytest tests/test_filled_symbols_runtime.py tests/test_motor_valve_runtime.py tests/test_primitive_scene_runtime.py
.venv/Scripts/python.exe -m compileall -q src tools tests
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

Für Runtime-Prüfungen wie im dokumentierten lokalen Defaultprofil
`IMAGE_CONVERTER_ISOLATE_SVG_RENDER=0` setzen; die ausdrücklich isolierten
Render-/Prozesstests bleiben dabei aktiv.
