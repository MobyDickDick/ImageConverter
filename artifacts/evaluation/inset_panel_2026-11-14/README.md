# DLG0016: gerundetes Verlaufspanel mit rechts abgeschnittenem Innenfeld

## Ursache und korrigierte Beschreibung

Die beiden aktiven XML-Quellen beschrieben DLG0016 fälschlich als zwei
blau/rote Pfeile („Wie AC0020“). Dieser Text aktiviert eine andere Symbolfamilie.
Der historische Dual-Arrow-KeyError und die spätere Rastereinbettung sind
separate Befunde; deren damalige Prozesskorrekturen lösten den Bild-/Textfehler
nicht. Das JPG bleibt unverändert.

Die Beschreibung in `artifacts/descriptions/Finale_Wurzelformen_V3.xml` und
`artifacts/images_to_convert/Finale_Wurzelformen_V3.xml` lautet jetzt:

> Im Hintergrund liegt ein waagerechtes Rechteck mit abgerundeten Ecken und einem
> vertikalen Graustufenverlauf: oben leicht heller, unten etwas dunkler. Davor
> liegt ein etwas kleineres weisses Rechteck, dessen linke Ecken abgerundet sind.
> Das weisse Vordergrundrechteck ist rechts bei ungefähr 90 Prozent der Breite
> des Hintergrundrechtecks senkrecht abgeschnitten. Dadurch bleiben oben, unten
> und links schmale graue Ränder sowie rechts ein breiterer grauer Bereich
> sichtbar. Keine Beschriftung oder weiteren Zeichen.

„Abgeschnitten“ beschreibt hier die gerade rechte Kante des weissen Innenfelds,
nicht einen Beschnitt des gesamten Bildes. Im JPG endet das Innenfeld bei etwa
87 Prozent der Bildbreite; „ungefähr 90 Prozent“ ist eine qualitative Angabe,
keine vorgegebene Rekonstruktionskoordinate.

## Zweite Ursache und Korrektur

Ein frischer CLI-Lauf mit dem korrigierten Text, aber ohne Modellergänzung
(`description_only/`), bleibt ein Entwurf. Der allgemeine Fallback erzeugt zwei
eckige Rechtecke und verlegt den Verlauf auf das nahezu weisse Innenfeld.
Die Kantenübereinstimmung liegt bei beiden Renderern unter 0,72.

Der neue `InsetPanel`-Fitter rekonstruiert diese beschriebene Kombination aus
den Rasterpixeln: ein gerundetes Hintergrundrechteck, zwei Graustufen-Endfarben
und ein weisses Vordergrundrechteck mit elliptischen linken Ecken und geradem
rechten Abschluss. Das SVG enthält zwei sichtbare native Vektorformen,
zwei Verlaufsstopps und keine Rastereinbettung. Die elliptischen Bögen sind
analytische Formparameter, keine nachgezeichneten Pixelkonturen.

Die Suche liest weder Katalog-IDs noch Sample-SVGs. Ein geschlossener
Beschreibungsvertrag weist zusätzliche Objekte und widersprüchliche Aussagen
zurück. Abmessungen und Farben werden am Original vermessen. Die Ergänzung
gilt für diesen beschriebenen Paneltyp; sie ist kein allgemeiner Nachweis für
beliebige Verschachtelungen oder Beschreibungsformulierungen.

## Abnahme

`after/` enthält die tatsächliche CLI-Ausgabe, den Validierungsstatus, das
Laufprotokoll und die Raster beider Renderer. Der vollständige Lauf meldet
`validated` und `satisfactory`. Beide Katalogansichten enthalten die korrigierte
Beschreibung und das neu gemessene SVG. Andere Katalogzeilen wurden weder neu
konvertiert noch neu vermessen; historische Beschreibungen in alten Laufbelegen
bleiben als Herkunft erhalten.

| Prüfung | Nur Textkorrektur | Mit Modellergänzung |
| --- | ---: | ---: |
| MuPDF: normierter Pixelfehler | 0,0002263 | 0,00005535 |
| librsvg: normierter Pixelfehler | 0,0002398 | 0,00005752 |
| MuPDF: Kantenübereinstimmung | 0,6769 | 0,9500 |
| librsvg: Kantenübereinstimmung | 0,6786 | 0,7277 |
| Pixelabnahme beider Renderer | fehlgeschlagen | bestanden |

Die vorhandenen Qualitätsgrenzen bleiben unverändert: MSE ≤ 0,01,
Vordergrund-MSE ≤ 0,04, Masken-IoU ≥ 0,85, Kantenübereinstimmung ≥ 0,72.
Zusätzlich prüfen lokale Regionen alle vier äusseren Ecken, beide linken
Innenecken und die rechte Schnittkante (95%-Fehlerquantil ≤ 12). Das Profil im
breiten grauen Bereich darf im 95%-Quantil höchstens 3 Tonwerte abweichen.
Innenfeld und maximale lokale Abweichung sichern zusätzliche dunkle Zeichen ab.
Die librsvg-Kantenmessung liegt nahe der Grenze; das gilt für diese kleinen
180 × 25 JPEG-Pixel und ist keine Zusage für weitere Grössen.

181 fokussierte Tests bestehen, darunter drei unabhängig mit OpenCV erzeugte
Raster mit unterschiedlichen Grössen, Rändern und Schnittpositionen sowie
Gegenproben für fehlendes Innenfeld, Zusatzzeichen, falsche Farben, umgekehrten
Verlauf, fehlende Rundungen und abgelaufenes Suchbudget.
Weitere 38 Tests für Katalogdaten, Klassen und Katalog-HTML bestehen ebenfalls.

Reproduktion aus dem Projektverzeichnis:

```powershell
.venv/Scripts/python.exe -m tools.convert_one_image DLG0016 --output-dir .tmp/inset-recheck
.venv/Scripts/python.exe -m artifacts.evaluation.inset_panel_2026-11-14.verify
.venv/Scripts/python.exe -m pytest -q tests/test_inset_panel_runtime.py tests/test_framed_panel_runtime.py tests/test_axial_panel_runtime.py tests/test_gradient_tube_runtime.py tests/detailtests/test_non_composite_runtime_helpers.py tests/detailtests/test_iteration_initialization_helpers.py
```

Messwerte: `summary.json`. Testprotokoll:
`artifacts/test-evidence/dlg0016_inset_2026-11-14.log`.
