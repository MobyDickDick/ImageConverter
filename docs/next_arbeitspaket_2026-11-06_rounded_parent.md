# Gerundete Verlaufsrechtecke im gemeinsamen Struktursuchweg

Teilpaket **SEARCH-STRUCTURE-ROUNDED-PARENT** von **SEARCH-STRUCTURE-01**,
Rang 1/P0. Ausgangscommit `fbb86fa59`. Fortsetzung des
[rechteckigen Elternteils](next_arbeitspaket_2026-11-05_rectangular_parent.md#sitzungslog).
Status: **Review**, synthetischer Teilabschluss mit gesondert offenem Rendererfehler.

Nachtrag 07.11.2026: Der separate
[Rendererteil](next_arbeitspaket_2026-11-06_rounded_renderer.md) korrigiert die
Eckgeometrie und besteht neue, vorab mit librsvg vorbereitete Referenzbilder.
Die hier berichteten Zahlen bleiben der unveränderte historische
MuPDF-Prüfstand; sie werden nicht in die neue Abnahme übernommen.

## Umfang und Umsetzung

Der gemeinsame Szenenvertrag verbraucht zusätzlich die ausdrückliche Aussage
„Das äussere Rechteck hat gerundete Ecken.“ Eltern- und Kindrundung sind
getrennte Anforderungen. Wiederholte, widersprüchliche und unbekannte Aussagen
bleiben Ablehnungen. Gemischte Kreis-/Rechteckkinder, Überdeckungsgruppen,
Einzelobjekte und optional helle Konturen verwenden dieselbe Strukturagenda.

Die mittleren Seitenabschnitte liefern den axialen Verlauf und die
Subpixelgrenzen. Vier unabhängig freiliegende Eckdefizite müssen eine
übereinstimmende positive Rundung tragen. Bei Kindrechtecken bleiben die
bisherigen zwei sichtbaren Eckbelege erforderlich. Die Eckenmessung arbeitet
auf begrenzten Bildausschnitten, damit verdeckte Ecken die Suche nicht durch
wiederholte Masken über das ganze Bild belasten.

Die äußere Silhouette schließt Löcher durch helle Kindkonturen vor der
Randsuche. Sonst würde deren Fläche fälschlich zur Elternkontur zählen.
Die Konturfarbe benötigt wie bisher Belege außerhalb der Mischlinie zwischen
Verlauf und Weiß; Rundungen verwenden die stärksten freiliegenden Farbvorlagen.
Die Breite wird aus der Randdeckung und dem gemessenen gerundeten Umfang geschätzt.

Der Flächendefizitwert ist ein Startwert für den nativen Radius. Der lokale
Renderer approximiert die Eckkurve anders als einen idealen Viertelkreis;
deshalb vergleicht die gemeinsame Registrierung dreizehn begrenzte Radius-
Startwerte mit den Originalpixeln. Sie verwendet denselben Rendercache,
Fehlerbestandsschutz, Auswertungszähler, Scheduler und dieselbe Bilddeadline.
Danach laufen die bisherige Verfeinerung und alle Objekt-/Relations-/Rastergates.
Vier eigene lokale Eckgates verhindern das Verdünnen kleiner Eckfehler durch
die große Elternfläche. Kinder müssen auch innerhalb der gerundeten Kontur liegen.

Es gibt kein neues Familienmodell und keinen Dispatch anhand einer Bildkennung.
Elternrundung gehört zur bildgebundenen negativen Evidenz. Acht Kinder,
96 Strukturzustände und fünf Sekunden je CLI-Bild bleiben die Grenzen.

## Abnahme

Zwölf synthetische Eingaben mit Seed `624873` wurden **vor** der Runtimeänderung
gerastert, annotiert und über die echte überwachte CLI ausgeführt. Derselbe
Input-/Beschreibungs-/Objektbestand besteht nachher **12/12 statt 0/12**.
Die Szenen enthalten drei bis sechs Kinder, gemischte Gruppen und Einzelobjekte,
beide Verlaufsachsen, verschiedene Seitenverhältnisse, Elternradien von zwölf
bis 32 Pixeln sowie optional Kindrundungen und helle Konturen.

Der zusätzliche Entwicklungsseed `981347` besteht **12/12**, die eine gekoppelte
Plan-B-Variantenkohorte mit Seed `853291` **17/17**. Alle 41 Ausgaben wählen den
gemeinsamen Szenenweg. Höchster normalisierter MSE: `0,00002999`, niedrigster
Vordergrund-IoU: `0,994742`, niedrigste Kantenausrichtung: `0,915592`.
Die unveränderten Grenzen bleiben `0,01`, `0,85` und `0,72`. Der längste
überwachte Bildlauf benötigt lokal `3,640` Sekunden; keine allgemeine Laufzeitgarantie.

Kohorten, endgültiges Regressionsergebnis und Quell-/Artefakthashes stehen unter
[`rounded_parent_v1`](../artifacts/evaluation/rounded_parent_v1/README.md).
Rohdaten bleiben lokal unter `.tmp/rounded-parent/`.

Die gemeinsame Szenen-/Evidenz-/Registrierungsregression besteht **1.070/1.070**
Prüfungen, Exit 0, ohne Überspringung. Sie enthält 49 der neuen Prüfungen;
die anschließend ergänzte Budget-/Cache-/Fehlerbestandsschutz-Gegenprobe
besteht separat **1/1**. Zusammen sind es 50 neue Prüfungen. Das separate
Kernprofil besteht **42/42**, Exit 0, ohne Überspringung. Der große Lauf endet
nach 754 Sekunden unter einem äußeren 1.500-Sekunden-Guard.
Python-Syntax, Diff- und Verweisprüfung sowie die schreibfreie historische
Reserveprüfung bestehen ebenfalls. Befehle, Exitcodes und Berichtshashes stehen
in [`checks.json`](../artifacts/evaluation/rounded_parent_v1/checks.json).

## Zusätzliche Gegenprobe mit unabhängigem Renderer

Die bisherige synthetische Vorbereitung und die produktiven Pixelgates verwenden
MuPDF. Die unabhängige native Objektprüfung bindet die Radien an die vorab
erzeugte Referenzgeometrie, ist aber kein zweiter Rasterrenderer.
`tools.audit_rounded_parent_renderers` prüft deshalb die gespeicherten Ausgaben
zusätzlich mit installiertem librsvg. Ergebnis: **41/41 Gesamtbilder**, aber nur
**121/164 lokale Elternecken** bestehen; dieselben Ecken bestehen mit MuPDF
164/164. 28 der 41 Bilder bestehen alle vier librsvg-Eckgates. Keine Grenze
wird gelockert; diese Gegenprobe ist ausdrücklich keine positive Gesamtabnahme.

Die Abweichung besteht schon ohne Konverter: Ein natives Rechteck mit `rx=30`
auf weißem Grund und gleichmäßiger Füllung hat analytisch einen Eckverlust von
`(1-pi/4)*30^2 = 193,1417` Quadratpixeln. Gemessen werden mit MuPDF `234,9529`,
mit librsvg `193,8471`. Die große Eckrundung des vorhandenen MuPDF-SVG-Wegs ist
damit eine eigenständige, reproduzierte Grenze. Der nächste P0-Schritt ist
[SVG-ROUNDED-RENDERER-01](next_arbeitspaket_2026-11-06_rounded_renderer.md).
Der neue Suchweg behebt diesen vorhandenen Rendererfehler nicht.

## Grenzen

Synthetische Entwicklung mit vollständig sichtbaren Elternrechtecken und vier
belegten Ecken. Angeschnittene Elternrechtecke, elliptische oder uneinheitliche
Ecken, beliebige Verschachtelungen und unabhängige reale Übertragung sind nicht
abgenommen. Die Kindzugehörigkeitsprüfung ist konservativ: Auch die äußere
Kindbox muss innerhalb des gerundeten Elternteils liegen.

HC0010 und Rail bleiben **sealed_unrun**, ohne Konvertierungsversuch und ohne
neue Abnahme. SEARCH-STRUCTURE-01, GENERAL-SCENE-COMPOSITION-09 und
GENERAL-SCENE-REAL-05 bleiben offen. Katalog und Konvertierungsarchiv bleiben
unverändert. Die lokale Umgebung verwendet Python 3.10.11; keine vollständige
Standardsuite und keine Archiv-Neukonvertierung.

## Reproduktion

Frische Zielordner verwenden. Für den Vorhervergleich die neu erzeugten
Eingaben im Ausgangsstand ohne `--require-all` ausführen.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_rounded_parent --prepare .tmp/round-parent-inputs-new --seed 624873
.venv/Scripts/python.exe -m tools.evaluate_rounded_parent --inputs .tmp/round-parent-inputs-new --output .tmp/round-parent-cli-new --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_parent --inputs .tmp/round-parent-inputs-new --output .tmp/round-parent-cli-new --verify-only --require-all
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_rounded_parent --seed 981347
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_rounded_parent --seed 853291 --variations
.venv/Scripts/python.exe -m pytest tests/test_rounded_gradient_parent.py tests/test_rectangular_gradient_parent.py tests/test_conversion_search_scheduler.py -q
.venv/Scripts/python.exe -m tools.audit_rounded_parent_renderers --inputs .tmp/round-parent-inputs-new --output .tmp/round-parent-cli-new --report .tmp/round-parent-renderers-new.json
```

## Sitzungslog

- Getestet: zwölf gepaarte CLI-Fälle, Zusatzseed, eine Variantenkohorte, 50 neue Positiv-/Gegenproben und die gemeinsame Szenen-/Registrierungsregression.
- Ergebnis: CLI 0/12 vorher, 12/12 nachher; Zusatzseed 12/12, Varianten 17/17; Regression 1.070/1.070, zusätzliche Budgetgegenprobe 1/1 und Kernprofil 42/42, jeweils Exit 0 ohne Überspringung.
- Grenzen: synthetische Entwicklung; zusätzliche librsvg-Eckprüfung nur 121/164, reale Gesamtabnahme und angeschnittene Elternrechtecke offen.
- Nächster Schritt: SVG-ROUNDED-RENDERER-01, die reproduzierte Eckabweichung des MuPDF-SVG-Wegs vor weiterer Komposition beheben. Danach SEARCH-STRUCTURE-CLIPPED-RECTANGULAR-PARENT. Reale Reserve erst nach vollständigem unabhängigen Prüfer freigeben.
- Startbefehl: `.venv/Scripts/python.exe -m pytest tests/test_rounded_gradient_parent.py tests/test_rectangular_gradient_parent.py -q`.
