# BENCHMARK-PRACTICAL-01: Vorbereitung und zwei echte CLI-Piloten

Branch: `codex/benchmark-practical-01-2026-10-21`.
Ausgangsstand: `bb7deb1b93c713b915cad5d003f587335a9007e4`.

## Ergebnis und Abgrenzung

Das Arbeitspaket ist **begonnen, nicht abgenommen**. Es gibt jetzt eine
reproduzierbare Vorbereitung mit 20 realen Entwicklungskandidaten, eingefrorenen
Originalrasterkopien, Beschreibungen und Runtime-/Konfigurationsprüfsummen.
Eine neue Ausführung überschreibt keine vorhandenen Belege.
`tools.prepare_practical_benchmark` prüft Eingaben und erneut gerenderte
Pilotausgaben; geänderte Beschreibungen, Raster, SVGs und unvollständige
Pilotberichte werden zurückgewiesen.

Die 20 Topologiebezeichnungen in `config/practical_benchmark_candidates.json`
sind **vorläufig**. Sie sind keine unabhängig geprüfte Familienannotation.
Alle Quellen stammen aus dem bestehenden Abnahmearchiv und sind deshalb
bekannte Entwicklung. Farb-, Größen-, Text- und Richtungsvarianten wurden
nicht als zusätzliche Familien aufgenommen. Ob die vorgeschlagenen Topologien
tatsächlich unabhängig sind, muss ein separater Annotation-/Abstammungsaudit
prüfen. Für die endgültige Messung fehlen neue gesperrte reale Prüffamilien.
Ein anderer Dateiname macht ein bekanntes Motiv nicht unbekannt.

Die Vorauswahl enthält unter anderem Ventil, Dreieckscheibe, Sehnen/T,
Sehnen/Spirale, Quadratgriff, Scheibe/Griff, Textscheibe, verschachteltes Panel,
Warnzeichen, Kreuz, Pfeil, Flamme, Haus, Haken und Achsendiagramm. Sie enthält
offensichtlich Inhalt außerhalb des begrenzten Kreis-/Rechteckszenenwegs;
auch diese Einordnung ist noch keine unabhängige Annotation oder Abnahme.

## Gemessener Entwicklungspilot

Zwei vor dem Pilot festgelegte bekannte Kandidaten laufen mit unveränderter
Runtime über die echte `semantic-only`-CLI. Suchseed 17, 64 angeforderte
Iterationen, fünf Sekunden festes inneres Suchbudget, 35 Sekunden äußere
Prozessgrenze. Diese kurze technische Probe ist kein Vergleich mit den späteren
60-Sekunden-Hauptläufen.

| Quelle | Neutrale ID | gesamte CLI-Zeit | normalisierter MSE | Vordergrund-IoU | Kantenwert | Pixelprüfung |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| AC0232_L | case_00 | 2,297 s | 0,002913 | 0,930155 | 0,788358 | bestanden |
| AC0840_L | case_07 | 2,016 s | 0,004861 | 0,862338 | 0,886131 | bestanden |

Die vorhandenen unveränderten Pixel-/Komplexitätsgrenzen gelten. Beide
gespeicherten SVGs wurden nach dem Lauf nochmals unabhängig gerendert.
Die Referenz-SVG-Zugriffsaudits enthalten keine gesperrten Zugriffsversuche.
Die Konvertierung erhält nur die verlustfrei als PNG gespeicherten Original-
JPEG-Pixel und die vorhandene eigenständige Beschreibung. Rastervorbereitung
liegt außerhalb der berichteten CLI-Zeit. Original-JPEG und PNG haben getrennte
Prüfsummen; ihre dekodierten Pixel werden bei der Gegenprüfung verglichen.

**Vollständige fachliche Abnahme: ausstehend.** Die Pilotberichte führen
`pixel_satisfactory` separat, `accepted=false` und `semantic_review=pending`.
Objekte, Beschriftung und Beziehungen wurden in diesem Paket nicht unabhängig
annotiert. Es gibt keine neue Katalogfreigabe und keine Aussage über
Zeitersparnis oder Überlegenheit gegenüber anderen Werkzeugen.

Umgebung: Windows, CPython 3.10.11, 14 logische CPUs,
Intel64 Family 6 Model 181 Stepping 0, NumPy 2.2.6,
OpenCV headless 4.14.0.94, Pillow 12.3.0 und PyMuPDF 1.26.7.
Die Rohberichte halten Befehle, Paketversionen, alle Versuche, Ausgaben,
Zugriffsaudits und Prüfsummen fest. Zwei Fälle rechtfertigen keinen
familienübergreifenden Median-/p95-Vergleich.

## Protokoll für die folgende Hauptmessung

Vor Änderungen an der Runtime sind folgende Punkte festzulegen und in einem
neuen finalen Manifest einzufrieren. Die jetzige Vorbereitung ist ausdrücklich
kein solcher vollständiger Studien-Freeze.

1. Mindestens 20 unabhängig abgegrenzte und annotierte reale Familien, davon
   mindestens fünf außerhalb des Kreis-/Rechteckvertrags. Abstammung,
   Vorverwendung und Entwicklungs-/Prüfstatus je Familie auditieren. Neue reale
   Prüffamilien separat sperren; alle Nachkommen bleiben in derselben Partition.
   Objekte, sichtbare Regionen, erwarteter Text und Beziehungen aus den Rastern
   annotieren. Die Annotationen liegen außerhalb der Konvertierungseingaben.
2. Zwei vorhandene externe Verfahren auswählen: einen Kontur-Vektorisierer
   und ein Verfahren für strukturierte SVGs. Noch sind **keine** Versionen oder
   Vergleichsverfahren ausgewählt/installiert. Ein zweiter Konturtracer gilt
   nicht automatisch als strukturiertes Verfahren. Native Elemente,
   Textdarstellung und Bearbeitbarkeit des tatsächlichen SVGs nachweisen.
   Lizenz, Version, Installationsbefehl und vollständige Einstellungen erfassen.
   Einstellungen ausschließlich auf Entwicklung festlegen.
3. Für die Hauptmessung vorab 60 Sekunden gesamte Laufzeit je Bild und
   Verfahren festlegen, einschließlich Start und verfahrenseigener
   Vorverarbeitung; unabhängige Bewertung anschließend separat messen.
   Software-/Hardwareversionen und Ressourcen erfassen. Identische Quellen
   bereitstellen; Beschreibungszugriff und Eingabeunterschiede explizit
   berichten. Feste Seeds und wechselnde Verfahrensreihenfolge verwenden.
   Äußere Prozessgrenzen und deren Start-/Abbruchaufwand ebenfalls erfassen.
4. Dieselben unabhängigen Pixel-, Kanten-, Objekt-, Text-, Beziehungs- und
   Regionsprüfungen auf alle tatsächlichen Ausgaben anwenden. Fehlende SVGs,
   Abbrüche und nicht unterstützte Formen bleiben im Nenner. Pfadanzahl,
   Pfadkommandos, native Elemente und Text zusätzlich berichten. Pfadgeometrie
   darf korrekt sein, ohne native Bearbeitbarkeit vorzutäuschen. Renderbarkeit
   allein ist kein Erfolg.
5. Rohwerte je Versuch, vollständige fachliche Akzeptanz je Familie sowie
   Laufzeit-Median und p95 über alle Versuche berichten. Laufzeiten von
   Fehlversuchen einbeziehen; zensierte Zeiten kennzeichnen. Seeds und Varianten
   sind keine zusätzlichen unabhängigen Familien. Archivzahlen, aktuelle
   Katalogquote und neue Prüfergebnisse bleiben getrennte Angaben.
6. Mindestens zehn vorab gewählte Familien durch dieselben menschlichen
   Bearbeiter bis zu denselben fachlichen Zielkriterien korrigieren bzw. von
   Hand nachzeichnen lassen. Aktives Prüfen, Beschreibungserstellung und
   Editieren getrennt stoppen. Reihenfolge wechseln; Übung und Personeneffekte,
   nicht erreichte Abnahme und ggf. Zeitlimits dokumentieren. Die vorbereitete
   CSV enthält 40 leere Messzeilen mit rotierender Reihenfolge für zehn
   Entwicklungskandidaten und vier Verfahren einschließlich Nachzeichnen.
   Sie muss nach finaler Familien-/Verfahrenswahl erneut eingefroren werden.
   Leere Zeitfelder sind fehlende Messungen, niemals null Sekunden.

Die erzeugte `annotations.template.json` und `manual_times.template.csv`
bleiben unveränderte Vorlagen. Ausgefüllte Arbeitskopien separat speichern;
die Verifikation erkennt Änderungen an eingefrorenen Dateien.
Das Werkzeug meldet bis zur separaten Hauptstudie immer `study_ready=false`
und die noch fehlenden Nachweise. Es führt keine externe Vergleichsstudie aus.

## Reproduktion

Ausgabeverzeichnisse müssen neu sein:

```powershell
.venv/Scripts/python.exe -m tools.prepare_practical_benchmark --prepare .tmp/practical01/prepared
.venv/Scripts/python.exe -m tools.prepare_practical_benchmark --verify .tmp/practical01/prepared
.venv/Scripts/python.exe -m tools.prepare_practical_benchmark --pilot .tmp/practical01/prepared --output .tmp/practical01/pilot-verified --cases case_00 case_07 --budget 5
.venv/Scripts/python.exe -m tools.prepare_practical_benchmark --verify-pilot .tmp/practical01/pilot-verified --prepared .tmp/practical01/prepared
.venv/Scripts/python.exe -m pytest -q tests/test_practical_benchmark_preparation.py tests/test_anytime_benchmark.py tests/detailtests/test_target_alignment_taskboard.py --basetemp=.tmp/practical01/pytest-targeted
```

Die vollständigen lokalen Belege stehen unter `.tmp/practical01/`; ein frischer
Checkout muss sie mit den Befehlen neu erzeugen. Der kompakte Bericht unter
`artifacts/evaluation/practical_benchmark_v1/` ersetzt diese Rohdaten nicht.

## Prüfung dieses Zwischenstands

29 gezielte Tests bestehen: Vorbereitung/Pilotprovenienz, vorhandener
Anytime-Prüfrahmen, Aufgabenverankerung und Bild-ID-Hardcoding-Nullprüfung.
Die ersten angrenzenden Tests im allgemeinen Windows-Sandbox-Tempverzeichnis
scheiterten an `os.replace`-Zugriffsrechten. Mit explizitem `--basetemp` unter
dem Repository bestehen sie ohne Codeänderung. Syntaxprüfung für `src`,
`tests`, `tools`, CLI-Hilfe und Whitespace-Prüfung mit der bestehenden
CRLF-Konvention bestehen. Die produktive Konvertierungslogik und die
gespeicherten Abnahmearchive wurden nicht geändert.

Die zusätzliche normale Standardsuite wurde mit folgendem Befehl gestartet;
beim Festhalten dieses Zwischenstands war sie noch nicht abgeschlossen.
Ein vollständiges PASS wird nicht behauptet. Fortschritt und Ergebnis liegen
in `.tmp/practical01/standard.log` und nach Abschluss in `standard.xml`:

```powershell
.venv/Scripts/python.exe -m pytest -q --maxfail=1 --basetemp=.tmp/practical01/pytest-standard --junitxml=.tmp/practical01/standard.xml
```
