# Vorhandene SVG-Bauteile zusammensetzen

Die Einzelkonvertierung unterstützt jetzt eine vollständige Liste vorhandener
SVG-Bauteile. Anders als „Form ähnlich wie …“ übernimmt sie deren tatsächliche
Vektorelemente einschliesslich Verläufen, Konturen und Text.

Im Feld **Bildbeschreibung** ersetzt eine solche Liste den bisherigen Freitext:

```text
SVG-Bauteil: AC0151_L.svg
SVG-Bauteil: AC1002_L.svg hinter AC0151_L.svg
```

Diese Dateinamen bezeichnen die Röhre und ein M-Symbol mit Griff nach links.
Mit `hinter` wird der Motor zuerst gezeichnet und sein Griff von der Röhre
verdeckt. Entsprechend ist `vor DATEINAME.svg` möglich. Die referenzierte Datei
muss genau einmal in der Liste stehen. Selbstbezüge, widersprüchliche und
mehrdeutige Ebenenangaben werden vor dem Start abgelehnt. Die Vorgabe gilt auch
bei fester Position, etwa `SVG-Bauteil: Motor.svg bei 80 165 skaliert 2.5 hinter Röhre.svg`.
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

Eine Zeile entspricht einer Instanz. Bis zu zwölf Instanzen sind möglich.
Ohne Ebenenvorgabe beginnt die Suche mit der Zeilenreihenfolge und vergleicht
auch andere Zeichenreihenfolgen am Originalbild. Explizite `vor`-/`hinter`-Angaben
bleiben verbindlich. Alle gemalten Flächen und Konturen müssen
vollständig auf die Zeichenfläche passen. Transparente Ränder einer Quelldatei
dürfen überstehen; dafür sind auch negative Positionen zulässig. Weisse Flächen
gelten als gemalt. Die Grösse der Originaldatei bleibt erhalten. Drehung,
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
Zusätzlich wird jeder Bereich mit überlappenden Bauteilflächen einzeln geprüft.
Sein normalisierter Pixelfehler darf wie der globale Fehler höchstens 0.01
betragen. So kann ein kleiner überstehender Griff nicht mehr im Gesamtbild
untergehen. Ein korrekt verdecktes Bauteil bleibt als vollständiger Vektor
erhalten. Auch gespeicherte ältere Bauteilergebnisse werden beim nächsten
Serverstart mit der neuen Prüfung neu bewertet.
Ein schlechter Bildvergleich bleibt ein **ungenügender Entwurf**. Die automatische
Platzierung sucht mit unverzerrt gerenderten Ausschnitten der gemalten
Bauteilflächen. Eine abschliessende Suche verfeinert Position und proportionale
Skalierung im zusammengesetzten Gesamtbild anhand derselben Qualitätsgrenzen
wie die Ausgabe. Feste Positionen bleiben unverändert. Die Suche bleibt begrenzt;
ähnliche Details, Überdeckungen,
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
automatisch wiedergefunden. Das Projekt-SVG `AC1002_L.svg` hatte ein verschobenes
M und eine abweichende Kreisfüllung. Dieses Bauteil ist anhand seines Originals
korrigiert; die vorherige Version liegt in der SVG-Historie. Seine eigene
Rasterprüfung besteht ebenfalls.

Zusätzlich verhinderte der transparente rechte Rand des Motor-SVGs die passende
Skalierung am rechten Bildrand. Die Suche begrenzt jetzt die gemalten Flächen
anstelle der gesamten Quellzeichenfläche und korrigiert anschliessend die
Position im Gesamtbild um einen halben Pixel. Die zusätzliche Vorgabe
`hinter AC0151_L.svg` verdeckt den Motorgriff korrekt. Der echte GUI-Worker
besteht die Gesamt- und lokale Prüfung: Vordergrund-IoU 0.9864,
Kantenübereinstimmung 0.7313, normalisierter Pixelfehler 0.0009081.
Im Überlappungsbereich sinkt der Fehler von 0.01817 auf 0.00003506.
Beschreibung und `AC0152_L.svg` sind im Projekt korrigiert.
[Ebenenangaben und lokale Prüfung](../artifacts/evaluation/ac0152_layers_2026-11-21/README.md).
Die [erste Korrektur](../artifacts/evaluation/ac0152_components_fix_2026-11-21/README.md)
dokumentiert den vorherigen Stand ohne die lokale Prüfung.

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
