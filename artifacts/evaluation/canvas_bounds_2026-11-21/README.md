# SVG-Ergebnis innerhalb der ursprünglichen Bildgrenze

Die Zeichenfläche bleibt so gross wie das ursprüngliche Bild. Sichtbare Flächen,
Konturen, Linienenden und Text dürfen darüber nicht hinausragen. Diese Bedingung
gilt auch für Entwürfe und Zwischenstände.

## Ursache und Korrektur

Das gemeldete `AC0253_2.jpg` ist 31 × 31 Pixel gross. Der gespeicherte Kreis hatte
einen Mittelpunkt bei `(15.784, 15.061)`, einen Radius von `14.873` und eine
Konturbreite von `0.892`. Einschliesslich der halben Konturbreite lag der obere
Rand damit bei `−0.258` und der rechte Rand bei `31.103` – ausserhalb des Bildes.
Die bisherige Rasterprüfung schnitt schon an der Bildgrenze ab und bemerkte den
unsichtbaren Überstand nicht.

`imageCompositeConverterCanvas` misst deshalb die vollständige Zeichnung auf
einer grösseren transparenten Fläche, vor dem Abschneiden am ursprünglichen
Bildrand. Gemessen wird das gesamte gemalte Alpha einschliesslich heller und
weisser Flächen, Konturen und Kantenglättung. Ein überstehendes Motiv wird als
zusammengehörende Baugruppe möglichst wenig verschoben und nötigenfalls
gleichmässig verkleinert. Die ursprünglichen Bildabmessungen und die vorhandene
viewBox bleiben erhalten. Formattribute, Farben und die Zahl der Zeichenelemente
bleiben bestehen. Es werden nur ein gemeinsamer Transformationsrahmen und die
verbindliche SVG-Viewport-Begrenzung ergänzt. Passende Motive erhalten keine
geometrische Verschiebung oder Skalierung.

Die gleiche Normalisierung läuft beim Rendern, bei Modellfreigaben, bei der
Auswahl einer Vorschau, beim Schreiben von CLI-/Sample-Ergebnissen und beim
Projekt-Export. Qualitätswerte und Validierungsbelege beziehen sich damit auf
die tatsächlich gespeicherte SVG-Version. Auch die Wiederherstellung eines
älteren CLI-Zwischenstands durchläuft die Grenze erneut. Alte überstehende
Projektversionen werden bei einer neuen Speicherung nicht allein wegen einer
knapp bestandenen, abgeschnittenen Rasterprüfung bevorzugt.

Es gibt keine zweite Rasterrekonstruktion und keine neue Elementerkennung für
diese Anpassung. Die Originale, hochgeladenen Vorlagen und historischen
Ergebnisse werden nicht nachträglich überschrieben.

## Nachweis

Der lokale Auftrag `74b82f6a7f6340fabd62b664039400a3` liefert den unveränderten
Ausgangsstand. Die gemalten Grenzen wurden bei vierfacher Rasterauflösung von
`(0.25, −0.5, 31.25, 30.5)` auf `(0, 0, 31, 31)` eingepasst. Die Zeichnung hat
weiterhin genau einen Kreis und ein Dreieck. Eine zusätzliche analytische
Prüfung des transformierten Kreisradius samt halber Konturbreite bestätigt,
dass der Kreis vollständig innerhalb der 31 × 31 Pixel liegt. Die Prüfung
entfernt die äussere Viewport-Begrenzung bei der Messung wieder; blosses
Abschneiden würde diesen Test daher nicht bestehen.

- [Kompakter Prüfstand](summary.json)
- [Lokaler ursprünglicher SVG-Stand](before.svg)
- [Lokal eingepasstes SVG](bounded.svg)
- [Lokales Testprotokoll](final_tests.log)

Die Tests prüfen ausser dem Pumpensymbol auch Kurven, weisse Flächen, Text,
gedrehte Gruppen, Linienenden, Konturen, nicht bei Null beginnende viewBoxen,
verschiedene Seitenverhältnisregeln und absichtlich beschnittene Linien. Sie
prüfen ausserdem Zwischenstände, gespeicherte Artefakte, Projekt-Backups,
Modellfreigaben und hochaufgelöste Kontrollrenderings.
Die Abschlussprüfung umfasst **256 bestandene Tests**. `git diff --check` und
die Nullprüfung für Bild-ID-Sonderfälle bestanden ebenfalls.

## Technische Grenzen

Für normale Geometrie wird im vorhandenen SVG-Renderer gemessen. Dessen
unvollständige Unterstützung von `slice` wird für die Messung durch eine
explizite Viewport-Abbildung ausgeglichen. Bei überstehenden Konstruktionen mit
Clip-/Maskenangaben wird, falls vorhanden, der lokale librsvg-Renderer für die
Messung verwendet, damit unsichtbare, absichtlich beschnittene Verlängerungen
das Motiv nicht unnötig verkleinern. Ist diese Messung nicht verfügbar, bleibt
die feste Viewport-Begrenzung aktiv. Ein solcher Fall blockiert den Start nicht.
Die Messauflösung und der Speicherbedarf sind begrenzt; die feste SVG-Grenze
verhindert auch bei nicht vollständig unterstützten SVG-Effekten sichtbaren
Überstand. Eine bestandene Randprüfung ersetzt keine Raster- oder
Beschreibungsprüfung.

Neue Worker verwenden die Änderung beim nächsten Konvertierungsversuch. Ein
Neustart des Webservers übernimmt zusätzlich die neuen Prüfungen im laufenden
GUI-Prozess und beim Projekt-Export. Laufende Aufgaben vorher abschliessen.
