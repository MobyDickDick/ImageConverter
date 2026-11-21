# AC0152_L: Motor hinter der Röhre und lokale Überlappungsprüfung

Die vorherige Ausgabe übermalte mit dem Motorgriff 56 Pixel der Röhre. Die
globalen Rastergrenzen wurden trotzdem erfüllt. Das war eine Lücke in der
Prüfung; eine bestandene globale Annäherung schloss diesen lokalen Fehler
nicht aus.

## Bedienung und Umsetzung

Die gespeicherte Beschreibung lautet jetzt:

```text
SVG-Bauteil: AC0151_L.svg
SVG-Bauteil: AC1002_L.svg hinter AC0151_L.svg
```

`vor DATEINAME.svg` ist ebenfalls zulässig. Die Ebenenangabe folgt auf den
Dateinamen oder auf eine feste Position und Skalierung. Das Ziel muss genau
einmal in der Bauteilliste stehen. Fehlende oder mehrdeutige Bezüge, Selbstbezüge
und zyklische Bedingungen werden vor dem Konvertierungsstart zurückgewiesen.
Die GUI erläutert die Syntax direkt bei „Vorhandene SVG-Bauteile zusammensetzen“.

Ohne Ebenenvorgabe beginnt die Suche mit der Zeilenreihenfolge und vergleicht
auch andere Zeichenreihenfolgen. Verbindliche Ebenenbezüge und feste Positionen
werden eingehalten. Die abschliessende Bauteilprüfung ordnet die unveränderten
Quellvektoren über ihre Instanzkennung zu und prüft die tatsächliche
Zeichenreihenfolge gegen alle Ebenenvorgaben.

Die gemeinsame Qualitätsprüfung misst jeden paarweisen Überlappungsbereich
zusätzlich lokal am Original. Verwendet werden die tatsächlichen Alpha-Flächen
der platzierten SVGs, einschliesslich weisser Füllungen und Quellen-Clipping.
Pixel mit Alpha über 64 zählen zur Fläche. Der normalisierte lokale Pixelfehler
darf wie der globale Pixelfehler höchstens 0.01 betragen. Die Prüfung steckt im
gemeinsamen Vektorkandidatenvergleich und wird auch bei der erneuten Prüfung
des gespeicherten SVG verwendet. Die lokale Abweichung wird zusätzlich in der
Reihenfolgen- und Positionssuche bewertet.

Es gibt keine AC0152-Sonderregel und keine Änderung der Quellvektoren. Der Griff
wird durch die vorgelagerte Röhre verdeckt; er wird nicht aus dem Motorbauteil
entfernt. Die Beschreibung wurde für genau dieses Original in beiden XML-Tabellen
gespeichert. Geschwistervarianten behalten ihre Beschreibungen.

## Nachweis am gemeldeten Original

`before.svg` hält die vorherige Projektversion fest. Deren erneute Prüfung in
`before_quality.json` ist jetzt **ungenügend**, obwohl die bisherigen globalen
Metriken weiterhin bestehen. Der vollständige neue GUI-Worker lief mit Profil
`quick`, Seed 42 und ohne Wiederverwendung des aktuellen SVG durch; er speicherte
die bessere Ausgabe regulär samt Sicherung der vorherigen Version ins Projekt.

| Prüfung | Vorher | Motor hinter Röhre |
| --- | ---: | ---: |
| Überlappende Pixel | 56 | 56 |
| Lokaler normalisierter Pixelfehler | 0.01817158 | 0.00003506 |
| Globaler normalisierter Pixelfehler | 0.00092146 | 0.00090810 |
| Vordergrund-IoU | 0.98635 | 0.98635 |
| Kantenübereinstimmung | 0.72614 | 0.73132 |
| Gesamtfreigabe mit lokaler Prüfung | ungenügend | bestanden |

Die sichtbaren übermalenden Griffpixel sind entfernt. Das separat aus der
Projektdatei gerenderte Ergebnis ist `final.png`. `comparison.png` zeigt von
links nach rechts Original, vorherige Ausgabe und korrigierte Ausgabe.
`gui_summary.json` protokolliert den echten Worker, `saved_quality.json` die
erneute Prüfung der endgültigen Projektdatei.
`automatic_order.json` belegt am gleichen Original, dass die Suche auch ohne
Ebenenvorgabe die Reihenfolge selbst korrigiert. Dabei wurden zur isolierten
Prüfung der Ebenensuche die bereits gemessenen Positionen fest vorgegeben.

Die Prüfung ist eine Rasterannäherung mit unveränderten SVG-Bauteilen, keine
allgemeine Freitextinterpretation und kein Beweis pixelidentischer Ausgabe.
Automatische Reihenfolgensuche bleibt durch das Zeitbudget begrenzt.

## Tests

```powershell
.venv/Scripts/python.exe -m pytest tests/test_svg_components.py tests/test_canvas_containment.py tests/test_description_language.py -q
```

**110 Tests bestanden**, einschliesslich des echten GUI-Workers und der erneuten
Qualitätsmessung des gespeicherten Ergebnisses. Die Syntaxprüfung sowie
`git diff --check` bestehen für die hier bearbeiteten Code-, Test-, Hilfe- und
SVG-Dateien.

`tests/test_svg_components.py` prüft die Korrektur einer kleinen Übermalung trotz
bestandener globaler Rasterprüfung, automatische Reihenfolgensuche, beide
expliziten Ebenenrichtungen, Ablehnung widersprüchlicher Bezüge, Durchsetzung der
Reihenfolge am tatsächlich gespeicherten SVG und einen ausdrücklich falsch
vorgegebenen Vordergrund. Letzterer wird eingehalten und bleibt ungenügend.
Ein weiterer Test weist veraltete erfolgreiche Workerberichte und zwischengespeicherte
GUI-Freigaben zurück. Der gemeldete reale Fall wird durch den echten GUI-Worker
mit nachfolgender Projektablage und erneuter Raster-/Bauteilprüfung getestet.

Ein zusätzlich begonnener Lauf mit dem gesamten `test_image_converter_gui.py`
zeigte weitere Fehler bei anderen Symbolen und wurde nach wiederholten Fehlern
abgebrochen. Die erste Abweichung betrifft `AC0030_L`: Der Test erwartet vier
direkte SVG-Kinder, während die aktuelle Zeichenflächenbegrenzung eine Gruppe
ausgibt; Bildprüfung und Konvertierung bestehen dabei. Die Abweichung wurde
separat auch mit der vorherigen GUI-Prüfversion 11 reproduziert. Der gesamte
GUI-Bestand wird deshalb ausdrücklich nicht als grün ausgewiesen. An diesen
anderen Konvertierungen wurde in diesem Paket nichts geändert.

Ältere erfolgreiche SVG-Bauteilergebnisse werden beim nächsten Serverstart mit
Prüfversion 12 erneut gemessen. Die Oberfläche muss nach diesem Codeupdate neu
gestartet werden, nachdem laufende andere Aufträge abgeschlossen sind.

Reproduktion des echten Laufs aus dem Projektverzeichnis:

```powershell
$env:PYTHONPATH='.'
.venv/Scripts/python.exe artifacts/evaluation/ac0152_layers_2026-11-21/run_gui.py
```
