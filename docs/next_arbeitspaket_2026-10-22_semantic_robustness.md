# SEMANTIC-ROBUSTNESS-01: reale Formulierungen und explizite Widersprüche

Branch: `codex/semantic-robustness-01-2026-10-21`.
Ausgangsstand: `7ed646e5f` auf `main`.

**Nachtrag 2026-10-22:** Die nachfolgend als offen bezeichnete Zeitauffälligkeit
ist inzwischen im [SEARCH-DEADLINE-OVERRUN-AUDIT](next_arbeitspaket_2026-10-22_deadline_overrun_audit.md)
mit Windows-Standbyereignissen korreliert und durch getrennte neue Phasenbelege
untersucht. Die ursprünglichen Versuche, Nenner und Qualitätsaussagen bleiben
erhalten; eine von Standby unabhängige Echtzeitgarantie wird nicht behauptet.

## Umfang

Zehn bereits bekannte reale Topologien werden mit unveränderten Originalpixeln
und neutralen Dateinamen geprüft: beschriftete Scheibe, Warnzeichen,
Diagonalkreuz, Rechtspfeil, verschachtelte Flammen, Kreuz auf Rechteck,
Streifenfläche, Haus, Sinusdiagramm und Bogen mit getrenntem Schaft.
Größen, Farben und Formulierungen zählen nicht als neue Familien.

`config/semantic_robustness_families.json` hält fünf explizit formulierte
Entwicklungsbeschreibungen und drei Negativfälle je Familie fest. Die Texte
und Raster wurden vor der ersten Runtime-Änderung eingefroren.
Eine separate Auswahl enthält zwei neue Beschreibungen und drei neue
Negativformulierungen je Familie. Sie wurde vor ihrer Auswertung eingefroren;
spätere Kompatibilitätskorrekturen wurden nicht anhand ihrer Ergebnisse gewählt.
Die frühere lokale Datei `final-formulations.json` ist eine nicht ausgewertete
Arbeitsfassung, kein zusätzlicher Prüfsatz.

Die Markierung der relevanten Rasterregionen und die Texte stammen vom
implementierenden Agenten, unabhängig von Detektorvorschlägen und Referenz-SVGs.
Das ist kein unabhängiger menschlicher Sprach-/Annotationsaudit und kein
Nachweis freien Sprachverständnisses. Die Prüfung deckt den hier beschriebenen
begrenzten Wortschatz und die dokumentierten Satzformen ab.

## Ergebnis des gepaarten Sprachvergleichs

| Prüfgruppe | Ausgangsstand | Neuer Stand |
| --- | ---: | ---: |
| Entwicklungsbeschreibungen | 23/50 | 50/50 in der vollständigen Wiederholung |
| Neue Prüfbeschreibungen | 6/20 | 20/20 |
| Explizit zurückgewiesene Entwicklungs-Negativfälle | 0/30 | 30/30 |
| Explizit zurückgewiesene neue Negativfälle | 0/30 | 30/30 |
| Familien mit vollständig bestandenem Entwicklungsumfang | 0/10 | 10/10 |
| Familien mit vollständig bestandenem neuen Prüfumfang | 0/10 | 10/10 |

„Explizit zurückgewiesen“ verlangt eine beobachtete `description_rejected`-
Diagnose und keinen internen Sucherfolg. Der Ausgangsstand meldet bei 19/30
Entwicklungs- und 6/30 neuen Negativfällen intern `search_satisfactory=true`.
Die übrigen Baseline-Negativfälle scheitern ohne diese neue Diagnose;
sie werden nicht als stille Erfolge bezeichnet. Der neue Stand meldet bei
keinem der 60 Negativfälle einen stillen Erfolg.

Ein vorausgehender vollständiger Entwicklungslauf desselben endgültigen Codes
bestand **49/50 Positivfälle und 30/30 Negativfälle**. Bei `item04p2` wurde kein
SVG erzeugt: Die Zeitaufsicht meldet **261,734 Sekunden**, zehn Sekunden
konfiguriertes Budget und **null Suchauswertungen**; auch die äußere nominelle
40-Sekunden-Grenze wurde überschritten. Die Ursache wurde nicht isoliert.
Dieser Versuch bleibt vollständig erhalten. Danach wurde der ganze
80-Versuche-Entwicklungssatz bei unverändertem Code, Seed und Budget wiederholt,
nicht nur der ausgefallene Einzelfall. Die Tabelle weist diese Wiederholung
aus; sie behauptet keine fehlerfreie Erstversuchsquote oder harte Zeitgarantie.
Einschließlich des vorausgehenden Laufs sind es 340 Sprach-CLI-Versuche.
Die Zusammenfassung enthält beide Läufe und den fehlgeschlagenen Versuch;
die Zeitauffälligkeit bleibt ein separater Untersuchungsbedarf.
Über alle Versuche des endgültigen Codes einschließlich dieser Wiederholung
bestehen **119/120 positive Versuche und 90/90 Negativversuche**. Der eine
fehlgeschlagene positive Versuch bleibt damit ausdrücklich im Gesamtnenner.

Diese Ergebnisse belegen die dokumentierte Sprachrobustheit auf bekannten
realen Familien, keine neue Bildfamilie, Katalogabnahme oder Zeitersparnis.

Der betroffene Regressionslauf besteht mit **900/900 Tests**, ohne Überspringen
oder erwartete Fehler. Die abschließenden 33 Grenztests bestehen ebenfalls;
32 davon überlappen mit dem Regressionslauf. Zusammen sind es **901 verschiedene
Test-IDs**. Der große gezielte Lauf dauerte 3.921,33 Sekunden. Die vollständige
normale Standardsuite wurde nicht zusätzlich ausgeführt. Syntaxprüfung für
`src`, `tests` und `tools`, CLI-Hilfe, Bild-ID-Hardcoding-Nullprüfung und die
Whitespace-Prüfung mit der bestehenden CRLF-Konvention bestehen.

Alle **377/377 Archiv-Neukonvertierungen** bestehen die bisherige absolute
Archiv-Pixelgrenze. Originalraster, gespeicherte SVGs und Index bleiben
hashgleich; alle 764 versionierten Archivdateien bleiben erhalten. Bei 42
Neukonvertierungen liegt der Fehler über dem historischen gespeicherten
Bestwert. Die absolute Abnahme behauptet deshalb keine Gleichheit mit jedem
Bestresultat und isoliert nicht die Ursache dieser Unterschiede.
Die gespeicherten besseren Ausgaben werden nicht ersetzt.

## Änderung

Der gemeinsame Sprachhelfer normalisiert gleichbedeutende Form-/Stilbegriffe,
Negationsvarianten und die lokale Orientierungssprache. Zitierte Beschriftungen
behalten Schreibweise und Groß-/Kleinschreibung. Die ursprünglichen Texte
bleiben in den Beschreibungsfragmenten erhalten. Im automatischen Kurztextweg
wird die ursprüngliche Schreibweise wieder an den Erkenner übergeben.

Verlaufsrichtungen werden an den Verlauf gebunden. Ein senkrechter Balken
belegt keinen senkrechten Verlauf. Bei seitlichen Bogen-Schaft-Motiven bleiben
Schaft- und Verlaufsrichtung getrennt. Für den unteren Bogen gelten sowohl
„Bogen unter Schaft“ als auch die inverse Beziehung „Schaft über Bogen“;
die Rasterprüfung entscheidet weiter über Geometrie und Farben.

Explizite Textanwesenheit bei gleichzeitigem Textverbot führt zu
`description_rejected`. Vordere/hintere Formselektoren werden in diesem
Sprachumfang nicht aufgelöst und deshalb ebenfalls konservativ abgelehnt. Die begrenzte
Zählgrammatik „Das Motiv enthält genau …“ bzw. „Es gibt genau …“ prüft native
Kreise, Rechtecke und Linien. Definitionen werden nicht mitgezählt. Diese
Grammatik beweist keine Objektzahl beliebiger Pfad-/Use-Konstruktionen und
keine frei formulierten Quantoren. Hintergrundrechtecke und der native
Kreispunkt eines Ausrufezeichens müssen bei solchen nativen Zählangaben
berücksichtigt werden.

Zähl- und Textabwesenheitsbedingungen werden vor der Artefaktausgabe geprüft.
Dieselben Bedingungen gelten vor der Übergabe eines frühen Erfolgskandidaten
an die Zeitaufsicht. Ein guter Pixelwert kann diese Bedingungen nicht umgehen.
Die Zusicherungen gehören zum jeweiligen Konvertierungs-/Suchkontext.
Auch bei historischer Referenzvererbung bleiben explizite Zählbedingungen
des aktuellen Aufrufers erhalten; sie dürfen nicht durch die Bedingungen
der Referenz ersetzt werden.
Die bisherigen Pixel-, Vordergrund-, Kanten- und Komplexitätsgrenzen bleiben
unverändert; das optionale Netz wird nicht aktiviert.

## Messung und unabhängige Prüfung

Die endgültigen gepaarten Versuche verwenden zehn Sekunden festes überwachtetes
Bildbudget, Suchseed 17 und 64 angeforderte Iterationen. Jeder CLI-Prozess hat
zusätzlich eine äußere Grenze von 40 Sekunden. Beide Stände bekommen dieselben
eingefrorenen Raster und Texte. Der Ausgangsstand wird mit `git archive` aus
dem genannten Commit exportiert; dieselben Binärabhängigkeiten und dieselben
Prüfwerkzeuge werden verwendet. Die Baseline-Versuche lesen keine neue Runtime.

Die Konvertierung erhält ausschließlich Raster und Beschreibung. Referenz-SVGs
sind in den Workern gesperrt. Der Prüfer kontrolliert Eingaben, gespeicherte
Ausgaben, Zeitaufsicht, Zugriffsbelege, vollständige Familienversuche und
Prüfsummen. Fehlende Ausgaben und Abbrüche bleiben im Nenner. Bereits von der
CLI verschobene Fehlquellen werden in deren Quarantäne wiedergefunden.

Jedes gespeicherte SVG wird unabhängig erneut gerendert und mit den bestehenden
strengen Pixel-/Komplexitätsgates geprüft. Zusätzlich gelten feste lokale
Rasterregionen mit normalisiertem MSE höchstens 0,03 und Kantenwert mindestens
0,55 sowie ein nativer Kreis-/Textvertrag. Dadurch werden kleine Merkmale
wie Beschriftung, Ausrufezeichen, Fenster und innere Flamme gesondert geprüft.
Die lokalen Zusatzgrenzen ersetzen keine bestehende globale Grenze.
Gesonderte Löschkontrollen entfernen innere Flamme, Fenster, Ausrufezeichenpunkt
und Beschriftung aus echten gespeicherten Ausgaben. Alle vier beschädigten SVGs
scheitern auch in den jeweils betroffenen lokalen Regionen. Der
Zusammenfassungsprüfer erzeugt diese Eingriffe beim erneuten Prüfen wieder.

Die ersten Fünf-Sekunden-Proben werden getrennt aufbewahrt. Eine davon enthält
eine mehrstündige Zeitlücke; weitere enthalten Zeitabbrüche. Ein anfänglicher
Callback-Bindungsfehler wurde korrigiert. Bei der Prüfannotation wurde der
Ausrufezeichenpunkt als zweiter nativer Kreis ergänzt und der negative
Zählfall von zwei auf drei Kreise korrigiert. Übereinstimmende Baseline-Ausgaben
wurden bytegleich kopiert und neu geprüft; geänderte/fehlende Fälle erneut
ausgeführt. Diese Diagnoseproben sind nicht der endgültige gepaarte Vergleich
und liefern keine Laufzeitbehauptung.

## Reproduktion

Alle Ausgabeverzeichnisse müssen neu sein. Die volle Messung erzeugt 260 echte
CLI-Versuche: 80 Entwicklung und 50 neue Prüfversuche pro Stand.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_semantic_robustness --prepare .tmp/wording-dev
.venv/Scripts/python.exe -m tools.evaluate_semantic_robustness --prepare .tmp/wording-final --selection config/semantic_robustness_final_formulations.json
.venv/Scripts/python.exe -m tools.evaluate_semantic_robustness --export-baseline .tmp/wording-parent --ref 7ed646e5f
.venv/Scripts/python.exe -m tools.evaluate_semantic_robustness --run .tmp/wording-dev --output .tmp/wording-before-dev --baseline .tmp/wording-parent --budget 10
.venv/Scripts/python.exe -m tools.evaluate_semantic_robustness --run .tmp/wording-final --output .tmp/wording-before-final --baseline .tmp/wording-parent --budget 10
.venv/Scripts/python.exe -m tools.evaluate_semantic_robustness --run .tmp/wording-dev --output .tmp/wording-after-dev --budget 10 --require-all
.venv/Scripts/python.exe -m tools.evaluate_semantic_robustness --run .tmp/wording-final --output .tmp/wording-after-final --budget 10 --require-all
.venv/Scripts/python.exe -m tools.evaluate_semantic_robustness --verify .tmp/wording-after-final --prepared .tmp/wording-final --require-all
```

Die vollständigen lokalen Belege einschließlich Diagnoseversuchen liegen unter
`.tmp/semantic01/`. Ein frischer Checkout muss sie erneut erzeugen. Kompakte
Ergebnisdateien ersetzen keine erneute Prüfung der vollständigen Ausgaben.
Der neue CI-Job `semantic-wording-robustness` prüft drei dieser realen Familien
einschließlich Negativfällen und erneuter Ausgabeverifikation. Ein entfernter
CI-Lauf wurde nicht gestartet.

BENCHMARK-PRACTICAL-01, GENERAL-SCENE-REAL-05, die produktive Netzabnahme,
IDO-19/IDO-21 und SEARCH-DEADLINE-COMPAT behalten ihren bisherigen Status.
Der Nachweis erweitert weder die Katalogzahl noch den allgemeinen Formumfang.
