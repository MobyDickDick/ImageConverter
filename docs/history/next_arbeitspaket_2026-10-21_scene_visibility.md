# Sichtbare Konturen, kombinierte Topologien und Tiefenbedingungen

Arbeitspaket: **GENERAL-SCENE-VISIBILITY-04**.
Branch: `codex/general-scene-visibility-04-2026-10-21`.
Ausgangsstand: `a11cbb791` auf `main`.

## Belegte Katalogzahl vor Beginn

Das Archiv enthält **377 abgenommene Originalbild-/SVG-Paare**, davon
329 im regulären `semantic-only`-Modus und 48 im historischen
`standard`-Kompatibilitätsmodus. Bezogen auf die dokumentierte Katalogbasis
von 1.785 Bildern sind das **21,1 Prozent**. Alle Bild-/SVG-Prüfsummen im
Index wurden vor Beginn überprüft; keine Abweichung.
Die aktuelle rekursive Zählung unterschiedlicher JPG-/JPEG-Dateinamen unter
`images_to_convert/` ohne `samples` bestätigt dieselben 1.785 Bilder.

Dies ist die nachgewiesene Untergrenze, keine neue Vollkatalog-Erfolgsquote.
Die synthetischen Szenen dieses Pakets erhöhen die Katalogzahl nicht.
Die 48 Kompatibilitätsfälle sind kein Nachweis einer ausschließlich aus Bild
und Beschreibung abgeleiteten Rekonstruktion.

## Umsetzung

`imageCompositeConverterSceneVisibility.py` erweitert den bestehenden nativen
Szenenweg für zwei bis drei einfarbig gefüllte Kreise/achsparallele Rechtecke
vor weißem Hintergrund. Jede Form kann eine eigene dunkle Kontur besitzen.
Sichtbare Füllgrenzen liefern Formvorschläge; Normalenabtastungen messen
Konturfarbe und -breite. Ein Kreis benötigt mindestens einen beobachteten
Halbbogen. Jede teilweise verdeckte Rechteckseite benötigt eigene sichtbare
Kontur mit weißem Außenbereich. Geschlossene native Grenzen ergänzen die
Erkennung vollständig sichtbarer verschachtelter Kinder. Die Ausgabe besteht
aus nativen `circle`-/`rect`-Elementen; detektierte Konturen werden nicht als
Pfade ausgegeben.

Vollständig verdeckte Rechteckseiten bleiben unbekannt. Der Algorithmus
ergänzt sie weder aus anderen Formen noch aus gespeicherten Vektoren.
Räumlich gleiche Vorschläge werden zu Instanzgruppen zusammengeführt;
unterschiedliche Formdeutungen bleiben Alternativen. Zusätzliche Instanzen
dürfen nicht für einen besseren globalen Pixelwert verschwinden.

Der gemeinsame `fit_scene_groups` prüft Formanzahl, tatsächliche native
Schnitt-/Verschachtelungsbedingungen und Zeichenreihenfolgen. Explizit benannte
Verschachtelung darf mit einer partiellen Überdeckung in derselben Szene
zusammenkommen. Die bisherigen vollständigen Szenenwege behalten ihre
Ausgaben, solange keine neue Überdeckungs-/Tiefenanforderung vorliegt.

Die begrenzte deutsche Grammatik unterstützt beispielsweise:

- „Die kleinere Form liegt vor der größeren Form.“
- „Die größere Form liegt hinter der kleineren Form.“
- „Die kleinste Form liegt innerhalb der größten Form. Die mittelgroße Form liegt vor der größten Form.“
- „Jede Form hat eine dunkle Kontur.“

Größenrollen müssen eindeutig sein: Die Außenflächen benachbarter Größen
müssen sich mindestens um den Faktor 1,12 unterscheiden. Zyklen,
Selbstbezüge, widersprüchliche Negationen und nicht modellierte Tiefenrollen
werden zurückgewiesen. Weißer Hintergrund wird vor der Tiefenauswertung
gesondert behandelt; die Fallnormalisierung berücksichtigt „ß“ → „ss“.

Bei überdeckenden Paaren muss die geforderte Reihenfolge außerdem in der sichtbaren gemeinsamen
Innenfläche gestützt sein. Dort wird die tatsächlich sichtbare Füllfarbe
geprüft, nachdem später gezeichnete Objekte ausgeblendet wurden. Ein guter
Gesamtpixelwert allein kann sonst eine falsch gezeichnete kleine Linse
durchlassen. Die bestehenden globalen und objektlokalen Qualitätsgrenzen
bleiben unverändert. Erkennung, Auswahl und Verfeinerung bleiben innerhalb
des überwachten CLI-Bildbudgets. Das optionale CNN wird nicht aktiviert.

## Nachweise

`tools.evaluate_visibility_scene` erzeugt native Referenzszenen unabhängig
von den Runtime-Erkennern. Die zwölf Entwicklungsszenen wurden vor der
Runtime-Änderung eingefroren und durch die damalige echte CLI konvertiert.
Nach dem letzten Runtime-Code-Freeze entstanden der neue gedrehte Prüfsatz
mit umformulierter Beschreibung und die erweiterte Vorlage.

| Prüfgruppe | Ausgangsstand | Neuer Stand |
| --- | ---: | ---: |
| Eingefrorene Entwicklungsszenen, Seed 20261021 | 0/12 | 12/12 |
| Neue gedrehte Prüfszenen, Seed 681293 | – | 12/12 |
| Dieselben Prüfraster unter neutralen Dateinamen | – | 12/12, SVGs bytegleich |
| Neue erweiterte Vorlage, Seed 924713 | – | 17/17 |
| Lokaler CI-Smoke, Seed 731829 | – | 6/6 |
| Frühere finale Fusionsszenen erneut durch die CLI | – | 12/12, SVGs bytegleich zum Vorpaket |
| Absichtlich falsche Tiefenangaben, Seed 41753 | – | 0/6 akzeptiert, erwartete Zurückweisung |

Jeder Erfolg verlangt eine unabhängig erneut gerenderte gespeicherte Ausgabe,
die bestehenden Pixel-/Komplexitätsgates und zusätzlich Anzahl, native
Formarten, Außenmaße (maximal 2,5 Pixel Abweichung), Zeichenreihenfolge
sowie jede Objektregion. Neuer finaler Prüfsatz, erweiterte Vorlage und
CI-Smoke verlangen zusätzlich die Konturbreite mit maximal 0,85 Pixel
Abweichung. Das ältere eingefrorene Entwicklungsmanifest enthält diese
zusätzliche Breitenannotation noch nicht. Ältere Objektprüfungen behalten
ihren Vertrag.
Beschädigte Konturen, gelöschte Kinder, vertauschte Reihenfolge und versteckte
Zusatzobjekte scheitern an der unabhängigen Objektprüfung.

Die CLI nutzt 64 angeforderte Iterationen, Suchseed 17 und fünf Sekunden
Bildbudget ohne Verlängerung. Der Prüfer verlangt den tatsächlich
beobachteten isolierten Budgetvertrag. Referenz-SVG-Lesezugriffe sind im
Konvertierungsworker gesperrt; die äußere Prozessgrenze beträgt 30 Sekunden.
Die sechs absichtlich widersprüchlichen Tiefenbeschreibungen sind eine
gesonderte Negativkontrolle und werden nicht als positive Prüfszenen gezählt.

Die kompakten Ergebnisse liegen unter
`artifacts/evaluation/visibility_scene_v1/`. Rohdaten mit Raster-/SVG-Paaren,
Runtime-Berichten und Referenzzugriffsbelegen liegen lokal in den unten
genannten `.tmp/visibility-*`-Verzeichnissen. Sie werden nicht versioniert.
Nach einem frischen Clone müssen sie mit den dokumentierten Befehlen neu
erzeugt und unabhängig geprüft werden. Die kompakte Zusammenfassung allein
ersetzt diese Prüfung nicht. CI lädt seinen vollständigen eigenen Lauf hoch.
Ein entfernter CI-Lauf wurde nicht gestartet.

Alle **377/377 Archiv-Neukonvertierungen** bestehen die bestehende absolute
Archiv-Pixelgrenze. Die 764 Archivdateien einschließlich Index bleiben
hashgleich. Keine Archivbeschreibung aktiviert den neuen Sichtbarkeitsweg.
Wie beim Vorpaket liegen 41 Neukonvertierungen über dem jeweils gespeicherten
historischen Bestwert; das absolute Archivgate behauptet keine Gleichheit
mit jedem Bestresultat. Gegenüber dem vorigen Archivlauf ändern sich drei
Messwerte: `AC0414_L` und `AC0421_S` nach unten, `AC0424_M` nach oben. Keiner
dieser Fälle aktiviert den neuen Szenenweg. Die Ursache dieser
Batchabweichungen wurde hier nicht gesondert nachgewiesen; die gespeicherten
besseren Ausgaben bleiben erhalten. Einzelwerte und Prüfzahlen stehen in
`checks.json`, der vollständige Lauf in `.tmp/visibility-archive-recheck/`.

## Reproduktion

```powershell
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --prepare .tmp/visibility-dev-inputs --seed 20261021 --count 12
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --inputs .tmp/visibility-dev-inputs --output .tmp/visibility-dev-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --prepare .tmp/visibility-holdout-inputs --seed 681293 --count 12 --rotate --paraphrase
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --inputs .tmp/visibility-holdout-inputs --output .tmp/visibility-holdout-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --inputs .tmp/visibility-holdout-inputs --output .tmp/visibility-holdout-cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --inputs .tmp/visibility-holdout-inputs --output .tmp/visibility-rename-cli --rename --require-all
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --prepare .tmp/visibility-plan-b-inputs --seed 924713 --count 3 --variations --paraphrase
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --inputs .tmp/visibility-plan-b-inputs --output .tmp/visibility-plan-b-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --prepare .tmp/visibility-ci-inputs --seed 731829 --count 6 --rotate --paraphrase
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --inputs .tmp/visibility-ci-inputs --output .tmp/visibility-ci-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --prepare .tmp/visibility-negative-final-inputs --seed 41753 --count 6 --contradict-depth
.venv/Scripts/python.exe -m tools.evaluate_visibility_scene --inputs .tmp/visibility-negative-final-inputs --output .tmp/visibility-negative-final-cli
.venv/Scripts/python.exe -m pytest -q tests/test_scene_visibility.py tests/test_scene_fusion.py tests/test_layered_scene_runtime.py tests/test_primitive_scene_runtime.py
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --output-dir .tmp/visibility-archive-recheck --max-cases-per-worker 60
```

Alle Läufe benötigen frische Ausgabeverzeichnisse. Der historische
`visibility-parent`-Lauf wurde vor der Runtime-Änderung erzeugt. Die
Zusammenfassung kann mit `python -m tools.summarize_visibility_scene_evaluation
--verify-only` gegen die vorhandenen vollständigen lokalen Läufe geprüft
werden; ein frischer Checkout besitzt diese Rohdaten nicht.

## Grenzen und Folgearbeit

Der Nachweis gilt für den beschriebenen begrenzten Kreis-/Rechteckvertrag,
deutlich unterscheidbare einfarbige Füllungen und sichtbare dunkle Konturen.
Er ist kein Nachweis freien Sprachverständnisses oder allgemeiner
Rekonstruktion realer Katalogfamilien. Konturen sind entweder für alle Formen
angefordert oder fehlen bei allen. Gleiche verdeckende Farben, stark
verdeckte Kreisbögen, unsichtbare Seiten, freie Farb-/Lagebezüge, Text,
Verläufe und weitere Formarten bleiben ohne allgemeinen Nachweis.

GENERAL-SCENE-REAL-05 führt als nächstes Paket unabhängig markierte unbekannte
reale Familien und eindeutig beobachtbare Farb-/Lagebezüge ein. Die offenen
Produktions-Netzabnahmen, IDO-19/IDO-21 und SEARCH-DEADLINE-COMPAT behalten
ihren bisherigen Status.

## Abschlussprüfungen

Die vollständige normale Standardsuite besteht mit **3.689 bestandenen
und 30 regulär übersprungenen Tests**. Alle **3719 gesammelten
Test-IDs** sind im vollständigen XML-Bericht enthalten. Die drei im
Standardprofil ausdrücklich ausgeschlossenen schweren Module wurden nicht
zusätzlich gestartet. Die betroffenen Szenentests bestehen mit 146 Tests;
die abschließende eigenständige Sichtbarkeitsprüfung besteht mit 30 Tests.
Zusammen decken diese gezielten Läufe 148 unterschiedliche Test-IDs ab.

Syntaxprüfung für `src`, `tests` und `tools`, CLI-Help, Bild-ID-Hardcoding-
Nullprüfung und die Whitespace-Prüfung unter Beachtung bestehender
CRLF-Zeilenenden bestehen. Prüfzahlen, Toolchain, Runtime- und
XML-Prüfsummen stehen in `checks.json`.
