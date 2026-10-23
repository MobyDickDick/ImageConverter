# Arbeitspaket â€“ U-Bogen mit Verlaufsschaft (2026-10-09)

Branch: `codex/ge9023-quality-2026-10-09`, Basis `dc10a763c`.
Das nÃ¤chste dokumentierte Ziel `GE9023_6M` besteht mit allen 14 Farb-/GrÃ¶ÃŸenvarianten
beide unverÃ¤nderten regulÃ¤ren QualitÃ¤tsgates ohne Pflichtmetrikregression.
Alle 14 bestehen auch die strengeren Plan-B-Pixelgrenzen. SVGs, eingefrorene
Vorher-Ausgaben, Manifest, Vergleichsbild und Nachweis stehen unter
`artifacts/evaluation/arc_shaft_recheck_v1/`.

## Beschreibung und allgemeine Registrierung

Die bisherige Katalogreferenz behauptete ein hellgraues Quadrat. TatsÃ¤chlich
zeigen alle 14 Bilder einen oben offenen U-Bogen Ã¼ber einem schmaleren,
abgesetzten senkrechten Verlaufsschaft. Beide XML-Kataloge beschreiben diese
Topologie jetzt eigenstÃ¤ndig, ohne Bildverweis oder numerische Formparameter.

Die Registrierung in `imageCompositeConverterArcShaft.py` verwendet ausschlieÃŸlich
Beschreibung und Raster. Zwei getrennte belegte Zeilenbereiche liefern Bogen und
Schaft. Zwei offene Arme, ihre Verbindung unten und der weiÃŸe Abstand sind
Pflichtevidenz. Die anfÃ¤nglichen Ellipsenradien, Strichbreite, Lage und Farbe
stammen aus dem Bogenraster. Die Schaftspalten und ihr lÃ¤ngskonstantes Farbprofil
liefern Rechteck und horizontalen Verlauf mit heller Mitte. Eine begrenzte
Grob-zu-fein-Suche verfeinert die Parameter mit gerenderten Pixeln. Sie benÃ¶tigt
hÃ¶chstens `1 + 16 Ã— 15 = 241` Renderproben und endet bei Stagnation frÃ¼her.
Nicht endliche Fehler, fehlendes Rendering, falsche Richtung, fehlende oder
zusÃ¤tzliche Objekte, verschobene SchÃ¤fte und falsche Topologien werden verworfen.
Die abschlieÃŸende BogenmaskenprÃ¼fung verlangt RasterunterstÃ¼tzung fÃ¼r die
analytische Ellipse. Ausgabe: ein nativer elliptischer SVG-Bogen, ein Rechteck
mit nativem Verlauf und weiÃŸer Hintergrund; keine exportierte Rasterkontur.

Der private Rechteck-Verlaufsadapter Ã¼berdeckte seine FarbbÃ¤nder um eine halbe
Quelleinheit. Bei schmalen SchÃ¤ften verschob dies das Farbprofil und die Kanten.
Der vorhandene Adapter fÃ¼r native Alphamasken unterstÃ¼tzt nun auch Rechtecke,
einschlieÃŸlich Rundrechtecken. Farben werden an Pixelmitten interpoliert und
mit der ursprÃ¼nglichen nativen Deckkraftmaske verbunden. Die gespeicherten SVGs
behalten ihre Vektorprimitive und VerlÃ¤ufe. Vier direkte PrÃ¼fungen sichern
horizontale/vertikale Interpolation und identische native Alphamasken.
Nicht unterstÃ¼tzte SVG-Eigenschaften verwenden weiterhin den bestehenden Pfad.

## Frische und reproduzierbare CLI-Abnahme

Vor jeder Runtime-Ã„nderung wurden alle 14 Originalbeschreibung-CLI-Ausgaben
unter neutralen Dateinamen eingefroren. Der Abnahme-Runner verwendet Seed 0,
`semantic-only`, getrennte Eingabekopien und einen Audit gegen Referenz-SVG-Zugriffe.
Nur die neue Registrierung und der neue Rechteck-Adapter sind im Vorher-Lauf
abgeschaltet. Alle reproduzierten Vorher-SVGs sind bytegleich mit dem echten
Vorlauf; dessen Dateien wurden nicht ersetzt. Beide Seiten werden nach demselben
End-SVG-Messvertrag bewertet. Die unabhÃ¤ngige SemantikprÃ¼fung verlangt den
unteren offenen Ellipsenbogen, den weiÃŸen Abstand und den schmaleren mittigen
Schaft mit heller Verlaufsmitte.

| Eingabe | mean_delta2 vorher | mean_delta2 nachher |
| --- | ---: | ---: |
| GE9023_1M | 11165.826172 | 231.920837 |
| GE9023_1S | 8342.599609 | 145.963333 |
| GE9023_2M | 10810.138672 | 202.837494 |
| GE9023_2S | 6443.546875 | 135.906662 |
| GE9023_3M | 7211.404297 | 91.800835 |
| GE9023_3S | 4334.153320 | 88.576668 |
| GE9023_4M | 4029.879883 | 46.059166 |
| GE9023_4S | 1986.083374 | 41.833332 |
| GE9023_5M | 7590.194824 | 135.134171 |
| GE9023_5S | 5441.653320 | 57.330002 |
| GE9023_6M | 13107.064453 | 253.677505 |
| GE9023_6S | 8491.113281 | 156.246674 |
| GE9023_7M | 9675.184570 | 137.023331 |
| GE9023_7S | 8066.799805 | 74.243332 |

**14/14 bestehen Good-Solution- und Quality-Complexity-Gate ohne
Pflichtmetrikregression; 14/14 bestehen auch die strengeren Plan-B-Pixelgrenzen.**
Zwei unabhÃ¤ngige CLI-Abnahmen reproduzieren alle 28 Vorher-/Nachher-SVG-Bytes
und sÃ¤mtliche Gate-Fallrecords. Beide melden null verbotene Referenz-SVG-Zugriffe.
Die spÃ¤tere PrÃ¤zisierung des Provenienztextes verÃ¤ndert nur den Manifest-Siegelhash,
keine SVGs, Metriken oder Entscheidungen. Alle 14 gelieferten Katalogausgaben
stimmen mit den tatsÃ¤chlich geprÃ¼ften CLI-SVGs Ã¼berein.

## Gekoppelte Plan-B-PrÃ¼fung und Grenzen

Vier eigenstÃ¤ndige synthetische Geometrien variieren Lage, Farbe, elliptische
Proportionen, Strichbreite und AuflÃ¶sung. Sie bestehen die Rasterregistrierung;
NegativfÃ¤lle und perfekte synthetische Vektoren kalibrieren die Abnahme.
Damit ist die geprÃ¼fte Topologie Ã¼ber die 14 Katalograster hinaus gestÃ¼tzt.
Es gibt keine passende Vorlage im bisherigen Sample-Pool. Der separate
Gesamtpool-Nachweis `PB-POOL-2026-10-07` bleibt offen.

Eine zusÃ¤tzliche echte CLI-Syntheseprobe mit dem unabhÃ¤ngigen SVG
`synthetic_holdout.svg` und Seed `20261009` besteht das Original sowie 11/16
zufÃ¤llige Varianten, insgesamt **12/17** strenge PrÃ¼fungen. Vier RestfÃ¤lle
verfehlen die Kantenmetrik; bei einer Variante nimmt die Runtime die Registrierung
nicht an. Die pixeloptimierende Suche und der Annahmefehler der Runtime haben
unterschiedliche Ziele. Diese offene StressprÃ¼fung wird als `GE9023-PB-STRESS`
weitergefÃ¼hrt; es wird keine vollstÃ¤ndige synthetische Plan-B-Abnahme behauptet.
Die Grenzen bleiben unverÃ¤ndert. CLI-Restfehlerwarnungen bleiben sichtbar.

## Reproduktion und Tests

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_arc_shaft_recheck artifacts/evaluation/arc_shaft_recheck_v1/manifest.json --output-dir .tmp/arc-shaft-reproduction
.venv/Scripts/python.exe -m tools.evaluate_arc_shaft_recheck .tmp/arc-shaft-reproduction/manifest.json --output .tmp/arc-shaft-gates.json
.venv/Scripts/python.exe -m pytest -q tests/test_arc_shaft_runtime.py tests/test_gradient_arrow_runtime.py tests/test_downward_gradient_arrow_runtime.py tests/test_filled_symbols_runtime.py tests/detailtests/test_rendering_gradient_compatibility.py
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q -ra --basetemp .tmp/arc-shaft-full-tests
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7.
178 fokussierte Tests bestehen, darunter 40 neue PrÃ¼fungen. SyntaxprÃ¼fung,
CLI-Hilfe und Runtime-ID-NullprÃ¼fung (`0 occurrences`) bestehen. Lokale Logs,
Eingabekopien und Wiederholungen liegen unter `.tmp/ge9023/`.
Der vollstÃ¤ndige Testabschluss wird nach Abschluss der laufenden Suite ergÃ¤nzt.

Der erneuerte Review enthÃ¤lt 1.000 EintrÃ¤ge, davon 993 renderbare Paare.
Alle 48 gespeicherten Erfolgsvarianten bleiben unter der Reviewgrenze.
Die 14 frisch akzeptierten FÃ¤lle sind aus der Rotation ausgeschlossen.
Die nÃ¤chste regulÃ¤re Aufgabe ist **`AC0413_1_M`**, gefolgt von `AC0713_1_L`,
`AC0721_1_S`, `AC0711_1_M` und `GE9014_1M`. Der genaue Review-Aufruf ist
im JSON-Nachweis gespeichert; historische Sammelausgaben bleiben erhalten.
