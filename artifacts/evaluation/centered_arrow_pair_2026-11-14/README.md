# AC0025: Beschreibung wirksam auswerten

Der alte Webauftrag `3d6890f5acde498682c2e37882fb70dd` hat den geänderten
Benutzertext korrekt gespeichert und an die CLI übergeben. Die Formulierungen
„Spitz gegen oben“ und „Spitz nach unten“ erreichten aber das bestehende
Linien-/Dreieck-Modell nicht: Die Erkennung verlangte „Spitze nach …“.
Dadurch lief die allgemeine Suche ohne den Dreiecksvertrag und lieferte erneut
den sichtbar falschen Kreis links. Ausserdem erkannte die Querlinienprüfung
„blaue horizontale Linie“, aber nicht „horizontale blaue Linie“.

Die begrenzte Sprachnormalisierung versteht jetzt beide Richtungsformulierungen.
Die Querlinienprüfung versteht beide Adjektivreihenfolgen einschliesslich
Flexionsendungen. Zitierte Beschriftungen bleiben unverändert; falsche
Richtungen und Farben sowie widersprüchliche Querlinienfarben werden geprüft.
Die GUI meldet identische SVG-Entwürfe nun auch bei geänderter Beschreibung.

Der neue Webauftrag `03d6a24c877c4b689924db009a8bbaf6` verwendet dieselben
Originalpixel, exakt denselben Benutzertext und dasselbe Suchprofil wie der alte
Auftrag. Er besteht nach 32,2 Sekunden die Qualitätsprüfung. Das SVG enthält
zwei schmale Rechtecke als vertikale Linien, zwei seitlich zentrierte Dreiecke
(links blau nach oben, rechts rot nach unten) und ein blaues Rechteck als
horizontale Querlinie. Keine Kreise, Rastereinbettungen oder Hintergrundobjekte.
Es wurde automatisch als `artifacts/converted_images/converted_svgs/AC0025.svg`
gespeichert. Der alte Auftrag bleibt erhalten.

| Prüfung | Vorher MuPDF | Nachher MuPDF | Nachher librsvg |
| --- | ---: | ---: | ---: |
| Normalisierter Pixelfehler | 0,003759 | 0,001752 | 0,001896 |
| Vordergrund-IoU | 0,8527 | 0,9517 | 0,9490 |
| Konturausrichtung | 0,8722 | 0,9880 | 0,9904 |

Die Geometrie und die Qualitätsgrenzen wurden nicht geändert. Die Querlinie
folgt der Rasterposition (etwa ein Drittel der Höhe von unten). Es gibt keine
neuen bildnamenspezifischen Geometrien oder Referenz-SVG-Abhängigkeiten.

`verify.py` prüft Quellpixel, unveränderte Beschreibung, gespeichertes Projekt-SVG,
Primitive, Farben, Zentrierung und beide Renderer. `summary.json` bindet die
Ergebnisse an die Quellhashes; `preview.png` zeigt Original, alten und neuen Stand.

```powershell
.venv/Scripts/python.exe artifacts/evaluation/centered_arrow_pair_2026-11-14/verify.py
.venv/Scripts/python.exe -m pytest -q tests/test_arrow_pair_runtime.py tests/test_description_language.py tests/detailtests/test_dual_arrow_runtime_helpers.py tests/test_image_converter_gui.py
```

Testnachweis: Zunächst 148 erfolgreiche Tests und vier durch Sandbox-Socket-/
Prozessbeschränkungen blockierte GUI-Tests. Diese vier bestehen beim erlaubten
Wiederholen ausserhalb der Sandbox. Nach Ergänzung von vier Flexionsfällen
bestehen alle 24 betroffenen Querlinien-/Benutzertext-Tests erneut; damit sind
156 unterschiedliche Tests erfolgreich geprüft, einschliesslich des echten
GUI-Konverterprozesses mit neutralem Dateinamen.

Die neue Meldung zu identischen Entwürfen wird nach dem nächsten regulären
Webserver-Neustart aktiv. Der laufende Hintergrunddienst wurde nicht beendet;
die Konverterkorrektur ist bereits in den neu gestarteten CLI-Aufträgen wirksam.
