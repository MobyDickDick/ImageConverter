# Vorhandene SVG-Bauteile zusammensetzen

Die Einzelkonvertierung unterstützt jetzt eine vollständige Liste vorhandener
SVG-Bauteile. Anders als „Form ähnlich wie …“ übernimmt sie deren tatsächliche
Vektorelemente einschliesslich Verläufen, Konturen und Text.

Im Feld **Bildbeschreibung** ersetzt eine solche Liste den bisherigen Freitext:

```text
SVG-Bauteil: AC0151_L.svg
SVG-Bauteil: AC1002_L.svg
```

Diese Dateinamen bezeichnen die Röhre und ein M-Symbol mit Griff nach links.
Der Konverter sucht für jedes angegebene Bauteil Position und proportionale
Skalierung im aktuellen Original. Die Auswahl der Bauteildateien bleibt manuell;
eine selbständige Suche nach passenden Bauteilen im gesamten Katalog ist noch
nicht implementiert. Es gibt keine motivspezifische Zuordnung im Programm.

Für eine feste Anordnung lässt sich die Position in **Originalbildpixeln** und
ein positiver Skalierungsfaktor vorgeben:

```text
SVG-Bauteil: AC0151_L.svg bei 0 0 skaliert 1
SVG-Bauteil: AC1002_L.svg bei 80 170 skaliert 2.4
```

Eine Zeile entspricht einer Instanz. Bis zu zwölf Instanzen sind möglich;
spätere Zeilen liegen vor früheren. Alle Instanzen müssen vollständig auf die
Zeichenfläche passen. Die Grösse der Originaldatei bleibt erhalten. Drehung,
Spiegelung, Neufärbung, Änderung einzelner Bauteile und ergänzender Freitext
werden in diesem Modus nicht unterstützt. Bei unklarer Syntax wird der Start
mit einer konkreten Meldung abgelehnt.

Exakte Dateinamen werden in dieser Reihenfolge gesucht:

1. `artifacts/converted_images/converted_svgs/`
2. `artifacts/samples/`
3. `artifacts/satisfactory_conversions/svgs/`

Es gibt keine Familienersetzung oder externen Dateiverweise. Das Ergebnis ist
ein eigenständiges SVG mit kopierten Vektoren. IDs, Farbverlaufsverweise und
Ausschnittgrenzen bleiben je Instanz getrennt. Aktive Inhalte und eingebettete
Raster werden wie bei SVG-Samples abgelehnt. Prozentwerte für Formkoordinaten
müssen zuvor in SVG-Einheiten umgewandelt werden. Prozentwerte in Farbverläufen
bleiben zulässig.

Die vollständige Bauteilliste ersetzt die natürliche Elementzählung. Eine
zusätzliche Prüfung vergleicht alle Bauteile mit den benannten Quellen:
zusätzliche, entfernte, umgefärbte oder verzerrte Elemente werden abgelehnt.
Die GUI prüft das tatsächlich gespeicherte SVG erneut gegen das Originalbild.
Ein schlechter Bildvergleich bleibt ein **ungenügender Entwurf**. Die automatische
Platzierung ist eine begrenzte Vorlagensuche; ähnliche Details, Überdeckungen,
kleine Motive und fehlerhafte Quellen können sie fehlleiten.

Das Protokoll enthält die verwendeten Dateien, SHA-256-Prüfsummen, Positionen,
Skalierungen und den Bildvergleich. Ändert sich später eine Quelldatei, kann die
Bauteilprüfung des alten Ergebnisses fehlschlagen; das Ergebnis selbst enthält
weiterhin seine kopierten Vektoren. Für die Darstellung und Bildprüfung wird
das bereits im Projekt verwendete `rsvg-convert` benötigt, auf diesem Windows-PC
unter `C:/msys64/ucrt64/bin/rsvg-convert.exe`. Damit stimmen Verlaufsmalerei und
Bauteilausschnitte mit einem vollständigen SVG-Renderer überein.

## Befund für AC0152_L

Die gespeicherte Projekt-Röhre `AC0151_L.svg` wird bei `(0, 0)` mit Faktor `1`
automatisch wiedergefunden. Das vorhandene Projekt-SVG `AC1002_L.svg` hat dagegen
ein verschobenes M und eine abweichende Kreisfüllung. Sein automatischer Einsatz
ergibt derzeit **keine bestandene Konvertierung von AC0152_L**. Es muss zuerst
ein korrektes passendes Bauteil bereitgestellt oder die Quelle berichtigt werden.
Die neue Funktion behebt die bisher fehlende Kombinationsmöglichkeit, bestätigt
diesen realen Fall aber ausdrücklich noch nicht als erfolgreich.

## Prüfung und CLI

`tests/test_svg_components.py` prüft automatische Platzierung an einer unabhängig
definierten Röhren-/Motor-Szene, getrennte IDs und Verläufe, unveränderten Text,
unerlaubte Änderungen, aktive und fehlende Quellen, erneute Pixelprüfung sowie
einen echten GUI-Auftrag über den separaten Worker mit ausgeschaltetem
„Aktuelles SVG weiterverwenden“.

Die gezielte Bestandsprüfung besteht mit 130 Sprach-/Rendererfällen und 18
GUI-Eingabe-/Startfällen. Zwei zusätzlich ausgeführte Bestandstests schlagen
auch mit den unveränderten Modulen aus Git-HEAD fehl:
`test_frozen_paired_line_template_keeps_vertical_shading_in_all_workbench_cases`
und `test_standalone_sample_refinement_enforces_resolved_reference_counts`.
Diese Bestandsfehler wurden für dieses Bauteilpaket nicht verändert.

```powershell
.venv/Scripts/python.exe -m src.imageConverterComponents --source ORIGINAL.png --description bauteile.txt --output zusammengesetzt.svg --seconds 30
```

Der reguläre CLI-Stapellauf und Plan B werden damit noch nicht um eine
automatische Bauteilauswahl erweitert. Nach dem Codeupdate den lokalen Webserver
nach Abschluss laufender Aufträge neu starten und die Browserseite neu laden.
