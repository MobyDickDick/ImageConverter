# Native gerundete Rechtecke korrekt rendern

**SVG-ROUNDED-RENDERER-01**, Status **Review**, synthetischer Abschluss am
07.11.2026 mit dokumentiertem zeitabhängigen Bestandsnachlauf. Reproduzierte
Rendererabweichung aus dem [gerundeten Elternteil](next_arbeitspaket_2026-11-06_rounded_parent.md).
Sie hat gemäß der verbindlichen Reihenfolge Vorrang vor weiterer Komposition.

## Reproduktion und Auswirkung

`tools.audit_rounded_parent_renderers` vergleicht gespeicherte synthetische
CLI-Ausgaben an ihren Originalrastern mit MuPDF und librsvg. Alle 41 Gesamtbilder
bestehen, aber nur 121/164 lokale Elternecken mit librsvg; mit MuPDF sind es
164/164. Die Gesamtfläche verdeckt die lokale Konturabweichung.

Der eingebaute analytische Kontrollfall braucht weder Konverter noch
Katalogquelle: ein gleichmäßig gefülltes natives Rechteck mit `rx=30`,
300 × 280 Pixeln und weißem Hintergrund. Soll-Eckverlust: 193,1417
Quadratpixel, MuPDF: 234,9529, librsvg: 193,8471. Die Abweichung gehört zum
vorhandenen Rendering und nicht zur neuen Topologiesuche.

```powershell
.venv/Scripts/python.exe -m tools.audit_rounded_parent_renderers --inputs .tmp/rounded-parent/inputs --output .tmp/rounded-parent/after --report .tmp/rounded-parent/renderer-replay-new.json
```

Die kompakte Gegenprobe samt Eingabe-/Ausgabehashes und allen Eckmetriken steht
in [`rounded_parent_v1`](../artifacts/evaluation/rounded_parent_v1/summary.json).
Die bestehenden synthetischen Raster und historischen Abnahmen unverändert
erhalten und als bisherigen MuPDF-Prüfstand kennzeichnen.

## Lieferumfang und Abnahme

1. Gerundete native Rechtecke im vorhandenen SVG-Rasterweg an einer korrekten
   beobachteten Eckgeometrie ausrichten; Füllung, Verlauf und Kontur gemeinsam
   prüfen. Keine Sonderbehandlung nach Familie oder Bildkennung.
2. Analytische Kontrollfälle und unabhängige librsvg-Raster für mehrere Radien,
   Subpixellagen, Größen, Seitenverhältnisse, Konturbreiten und Verlaufsachsen
   **vor** der Renderingänderung sichern. Scharfe Rechtecke und vorhandene
   andere SVG-Primitive als Gegenkontrollen beibehalten.
3. Neu vorbereitete synthetische Szenen und die bereits eingefrorenen Szenen
   getrennt ausweisen. Keine stillschweigende Neugenerierung alter
   Eingabeprüfsummen oder Übernahme historischer Erfolgsmengen.
4. Echte CLI, unabhängige native Radius-/Objekt-/Relationsprüfung sowie globale
   und vier lokale Eckgates verlangen. Bestehende Grenzen, fünf Sekunden
   Bildbudget und 96 Strukturzustände bleiben verbindlich.
5. Gemeinsame Registrierung einschließlich Radiusstartwerten erneut messen.
   Keine Korrektur eines Rendererfehlers durch dauerhaft falsche native Radien.

HC0010 und Rail bleiben gesperrt und ungetestet. Nach diesem Paket folgt der
bereits erkannte nächste Kompositionsteil **SEARCH-STRUCTURE-CLIPPED-RECTANGULAR-PARENT**:
angeschnittene äußere Rechtecke anhand sichtbarer Seiten-/Eckbelege anbinden,
fehlende Grenzen ohne ausreichende Beobachtung konservativ ablehnen.

## Umsetzung am 07.11.2026

Ausgangscommit `409b451f7`. Der MuPDF-Rechteckkurzweg wird ausschließlich im
privaten Renderdokument durch einen geschlossenen Pfad ersetzt. Jede
Viertellipse verwendet zwei kubische 45-Grad-Segmente. Das beseitigt die
falsche Eckform für Füllung und Kontur; derselbe Pfad erzeugt die Alphamaske
der vorhandenen Verlaufskompatibilität. Gespeicherte Konvertierungs-SVGs
behalten native `rect`-Elemente, die beobachteten Radien und ihre Verläufe.

Fehlendes `rx`/`ry` wird gemäß dem jeweils anderen Radius ergänzt, übergroße
Radien werden an der halben Seitenlänge begrenzt. Numerische Längen und `px`
sind im Pfadadapter unterstützt. Ungültige, scharfe oder nicht aufgelöste
Geometrien verbleiben beim vorhandenen SVG-Reader. Attribute für Farbe,
Kontur, Transformation, Kennung und Zeichenreihenfolge bleiben erhalten.
Nicht aufgelöste Stylesheets und animierte Geometrien werden nicht umgeschrieben.

Die vorab eingefrorenen Kontrollen enthalten auch diagonale Verläufe auf
länglichen Flächen. Sie deckten zusätzlich auf, dass `objectBoundingBox`
in einem Einheitsquadrat projiziert werden muss, bevor es auf die Objektbox
skaliert wird. Der gemeinsame Verlaufsadapter berücksichtigt diese Abbildung
jetzt; `userSpaceOnUse` behält seine Projektion in Benutzerkoordinaten.

Die Radiusregistrierung verwendet fünf symmetrische Startwerte zwischen 95
und 105 Prozent des gemessenen Flächendefizitradius. Die bisherige asymmetrische
Spanne von 75 bis 105 Prozent mit dreizehn Startwerten ist entfernt. An allen
41 neuen unabhängigen Referenzbildern liegen die Vorschläge zwischen -0,1530
und +0,2575 Pixeln zum Sollradius (höchstens 1,77 Prozent). Der größte
Radiusfehler der endgültigen nativen CLI-Ausgaben beträgt 0,2575 Pixel;
das bisherige unabhängige Radiusgate von 1,25 Pixeln bleibt bestehen.
Cache, Fehlerbestandsschutz, Deadline und Scheduler werden gemeinsam genutzt.

Die Szenenregression deckte zusätzlich auf, dass die hellsten fünf Prozent
einer Kontur noch viele Mischpixel enthalten können. Die Farbvermessung
bevorzugt deshalb die hellste Farbgruppe innerhalb einer Intensitätseinheit
nur dann, wenn mindestens fünf verschiedene Originalpixel sie belegen.
Bei weniger Belegen gilt weiter die bisherige konservative Schätzung.
Farbrekonstruktionsgrenze, zwei freie Kinderecken und vier freie Elternecken
bleiben unverändert. Die betroffenen dicht überlappenden Konturfälle bestehen
wieder die vollständigen unabhängigen Objekt- und Rastergates.

Drei früher dynamisch als negativ gerasterte Tiefenfälle werden mit korrekten
Ecken und belegter Konturfarbe jetzt positiv geprüft. Das ursprüngliche
`probe_04`-Raster des gleichfarbigen Seeds 372851 bleibt zusätzlich bytegenau
als historische Testdatei erhalten; auch dessen vollständige native und lokale
Pixelprüfung besteht mit der korrigierten Farbmessung. Ein separater Test
prüft die frisch gerasterte Darstellung. Direkte Kontrollen am eingefrorenen
unabhängigen Raster verlangen weiterhin mindestens zwei freie Ecken:
null/eine wird abgelehnt, zwei bis vier liefern den gemessenen Radius.

## Neue unabhängige Abnahme

Vor der Rendereränderung wurden die librsvg-PNGs, Quell-SVGs, Markierungen,
Beschreibungen und alten MuPDF-Vergleichsraster gesichert. Die Kontrolle umfasst
24 gerundete Fälle (18 unterschiedliche SVGs, sechs Wiederholungskontrollen)
sowie vier Gegenkontrollen für scharfe Rechtecke, Kreise, Ellipsen und Pfade.
Radien, Subpixellagen, Größen, Seitenverhältnisse, getrennte `rx`/`ry`,
Konturbreiten und Verlaufsachsen variieren. Die exakten unabhängigen
Kontroll-PNGs liegen in `tests/fixtures/rounded_renderer/`; Tests brauchen
keine installierte librsvg-Laufzeit und erzeugen ihre Referenzen nicht neu.

| Prüfung am unveränderten unabhängigen Raster | Vorher | Nachher |
| --- | ---: | ---: |
| Globale Kontrollgates | 23/28 | 28/28 |
| Lokale Kontrollecken | 40/96 | 96/96 |
| Primäre echte CLI, Seed 624873 | 2/12 | 12/12 |
| Zusätzliche echte CLI, Seed 981347 | nicht erneut als Vorherlauf beansprucht | 12/12 |
| Eine gekoppelte CLI-Variantenkohorte, Seed 853291 | nicht erneut als Vorherlauf beansprucht | 17/17 |

Alle 41 neuen CLI-Ausgaben bestehen die unabhängige native Objekt-, Radius-,
Box-, Kontur-, Verlaufs-, Eltern- und Reihenfolgeprüfung sowie globale und
objektlokale Rastergates. Beide Renderer bestehen zusätzlich je **164/164**
Elternecken. Beide Vektorzugriffswächter bleiben aktiv. Die überwachte
Prozesszeit beträgt höchstens 4,672 Sekunden im endgültigen lokalen Lauf;
fünf Sekunden Bildbudget und 96 Strukturzustände bleiben unverändert.
Das ist keine allgemeine Laufzeitgarantie.

Der analytische Kontrollfall mit Radius 30 hat weiterhin einen idealen
Eckverlust von 193,1417 Quadratpixeln. MuPDF verbessert sich von **234,9529**
auf **192,6824**; unabhängiges librsvg misst **193,8471**. Zusätzliche Tests
prüfen analytische Flächen für mehrere Radien und Auflösungen, elliptische
Ecken, fehlende Radiusattribute, Begrenzung, Subpixellagen und Transformationen.
Scharfe Rechtecke, Kreise, Ellipsen und Pfade bleiben in der direkten nativen
Pixelgegenprobe bytegleich. Der separate Renderworker liefert dieselben
korrigierten Pixel wie der Inprozessweg.

## Regression und Testsignal

Die gemeinsame Szenen-, Evidenz-, Registrierungs-, Renderer-, Worker- und
Budgetregression beendet **1.206 von 1.207** Prüfungen erfolgreich, ohne
Überspringung, Exit **1**, nach 651,57 Sekunden unter einem äußeren
2.400-Sekunden-Guard. Ein vorhandener Acht-Objekte-Fall mit wiederholten
Füllungen liefert im langen Lauf nach 5,149 Sekunden kein Ergebnis beim
unveränderten Fünf-Sekunden-Bildbudget. Derselbe Fall besteht im isolierten
Aufruf (1/1); anschließend besteht sein gesamtes Modul **32/32**, Exit **0**,
ohne Überspringung. Der Vergleich der JUnit-Knoten bestätigt, dass genau der
fehlgeschlagene Fall im Nachlauf besteht. Der primäre Exit 1 bleibt erhalten;
die Laufzeitgrenze ist damit ausdrücklich dokumentiert.

Das separate Kernprofil besteht **42/42**, Exit 0, ohne Überspringung.
Die gezielte Tiefen-/Kontur-/Beobachtungsprüfung besteht **140/140**, Exit 0;
eine zusätzliche Gegenprobe zum falsch kompensierten nativen Radius besteht
1/1. Diese Prüfungen verwenden den endgültigen Runtimecode beziehungsweise
sind durch die gemeinsame Regression ebenfalls abgedeckt. Keine Qualitäts-
oder Budgetgrenze wird für einen Nachlauf erhöht. Syntax, neue Verweise,
JSON-/Diffprüfung, aktuelle Runtimehashes und die schreibfreie Prüfung der
realen Sperrreserve bestehen. Befehle, Rückgabecodes und JUnit-Prüfsummen
stehen in `rounded_renderer_v1/checks.json`.

Ein historischer Variantenlauf wurde während einer längeren Laufunterbrechung
mit einem Konvertierungstimeout und fehlendem Zugriffsnachweis unvollständig.
Er bleibt als negativer Entwicklungsbeleg erhalten. Die vollständige
Wiederholung in einem frischen Ordner ist separat mit Exit 0 und allen
17 erwarteten nativen Radiusablehnungen dokumentiert.

## Historischer Prüfstand und Grenzen

Die 41 MuPDF-Eingaben und ursprünglichen CLI-Ausgaben vom 06.11.2026 werden
weder neu gerastert noch ersetzt. Ihre damalige Abnahme bleibt als
**historischer MuPDF-Prüfstand** mit der bekannten unabhängigen Lücke
121/164 erhalten. Das neue Paket erstellt gesonderte schreibfreie
Gegenprüfungen und neue CLI-Ausgaben zu diesen unveränderten alten Rastern.
Die neuen CLI-Läufe auf denselben 41 alten Rastern bestehen alle globalen
und 164/164 lokalen Eckenprüfungen mit beiden Renderern. Ihre nativen
Elternradien müssten aber um 1,2548 bis 3,3693 Pixel von der damals
annotierten Geometrie abweichen. Die unabhängige native Prüfung lehnt deshalb
alle 41 ab: **0/41 abgenommen**. Diese negativen Vergleichsläufe werden
ausdrücklich nicht als neue Abnahme oder als neue Referenz gespeichert.
Eine eigene Gegenprobe zeigt ebenfalls: Ein um zwei Pixel falscher Radius
kann das globale Pixelgate bestehen und muss trotzdem am nativen Gate scheitern.
Die vollständigen historischen Vergleichszahlen stehen separat in der Evidenz.

Die korrigierte neue Abnahme ist synthetisch. Es gibt keine pauschale
Archivneukonvertierung, keine neue reale Familienabnahme und keine Lockerung
eines Gates. HC0010 und Rail bleiben `sealed_unrun`, ohne Konvertierungsversuch.
SEARCH-STRUCTURE-01 und die übergeordneten Kompositions-/Realabnahmen bleiben
offen. Die lokale Umgebung verwendet Python 3.10.11; die vollständige
Standardsuite ist nicht Teil dieses Pakets.

## Reproduktion der korrigierten Prüfung

Frische Zielpfade verwenden. `--prepare` des Rendererwerkzeugs sichert neue
Kontrollen und drei unabhängige Szenenkohorten; es überschreibt keine Referenz.
Für die alltägliche Kontrolle sind die bereits gespeicherten Test-PNGs zu verwenden.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_rounded_renderer --controls tests/fixtures/rounded_renderer --report .tmp/rounded-controls-new.json --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_parent --prepare .tmp/rounded-independent-new --seed 981347 --reference-renderer librsvg
.venv/Scripts/python.exe -m tools.evaluate_rounded_parent --inputs .tmp/rounded-independent-new --output .tmp/rounded-independent-cli-new --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_renderer --inputs .tmp/rounded-independent-new --output .tmp/rounded-independent-cli-new --report .tmp/rounded-independent-audit-new.json --require-all
.venv/Scripts/python.exe -m pytest tests/detailtests/test_rounded_renderer.py tests/detailtests/test_rendering_gradient_compatibility.py tests/test_rounded_gradient_parent.py tests/test_rectangular_gradient_parent.py -q
```

CI prüft die eingefrorenen Kontrollraster, Render- und Szenenregressionen,
einen neu mit librsvg vorbereiteten Zusatzseed und alle vier Elternecken
der echten CLI-Ausgaben mit beiden Renderern. Rohdaten und Logs bleiben
lokal unter `.tmp/rounded-renderer/`; kompakte Prüfsummen, Berichte und
Befehle stehen in
[`rounded_renderer_v1`](../artifacts/evaluation/rounded_renderer_v1/README.md).
Danach folgt
[SEARCH-STRUCTURE-CLIPPED-RECTANGULAR-PARENT](next_arbeitspaket_2026-11-07_clipped_rectangular_parent.md).

## Sitzungslog

- Getestet: vorab eingefrorene librsvg-Kontrollen, 41 neue echte CLI-Fälle, 41 unveränderte historische CLI-Eingaben und gemeinsame Regression samt Nachlauf.
- Ergebnis: Kontrollen 28/28 und 96/96 Ecken; neue CLI 41/41 und je 164/164 Ecken; Regression 1.206/1.207, betroffener Modulnachlauf 32/32, Kernprofil 42/42.
- Grenze: ein zeitabhängiger Bestandstest im langen Lauf; synthetische Abnahme, historische Falschradius-Eingaben 0/41, reale Reserve ungetestet.
- Nächster Schritt: SEARCH-STRUCTURE-CLIPPED-RECTANGULAR-PARENT nach sichtbaren Seiten-/Eckbelegen; allgemeine Komposition und reale Gesamtabnahme bleiben offen.
- Startbefehl: `.venv/Scripts/python.exe -m pytest tests/test_rectangular_gradient_parent.py tests/test_rounded_gradient_parent.py tests/test_clipped_gradient_parent.py tests/detailtests/test_rounded_renderer.py -q`.
