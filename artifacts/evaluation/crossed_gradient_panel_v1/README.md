# Graues Verlaufspanel mit Diagonalkreuz und Minus

Die ursprüngliche Katalogbeschreibung für AC0110 nennt drei horizontale Linien.
Das passt zum Grundbild AC0110.jpg, aber nicht zu den Größenvarianten L/M/S.
Diese drei Bilder erhalten deshalb eine bildspezifische Ersatzbeschreibung aus
der korrigierten Benutzerangabe. Die Beschreibung des Grundbilds bleibt erhalten.

Ein frischer CLI-Lauf mit der ursprünglichen Beschreibung reproduziert den
Entwurf: unterbrochene Diagonalkonstruktion, fehlendes Minus und ungenauer
Verlauf. Der neue allgemeine Raster-Fit beobachtet den rechteckigen Rahmen,
beide vollständigen Diagonalen und das separate Minus unabhängig voneinander.
Ein Clip begrenzt die Linien am Rechteck; zwei durchgehende native SVG-Linien
verhindern Unterbrechungen an der Kreuzung. Der dreistufige horizontale Verlauf
hat einen frei angepassten hellsten Punkt links der Mitte. Alle Füllfarben
bleiben heller als der Rand. Die Ausgabe enthält sieben native Formen.

Die unveränderten globalen Rastergates werden durch lokale Prüfungen für beide
Diagonalen, das Minus und das Helligkeitsprofil ergänzt. Ein fehlender Arm,
eine deutliche Unterbrechung, ein fehlendes Minus, ein flacher Verlauf und ein
entgegen der Beschreibung rechts liegendes Maximum werden zurückgewiesen.
Es gibt keine Bild-ID-Sonderbehandlung und keinen Zugriff auf Referenz-SVGs.
Die Qualitätsgrenzen und das Erfolgsarchiv bleiben erhalten.

## Nachweis

`summary.json` vergleicht frische CLI-Ausgaben auf identischen JPEG-Bytes.
Der normalisierte RGB-MSE sinkt von 0,0134272 auf 0,0001180, um 99,1 %.
Die Konturdeckung steigt von 0,6849 auf 0,9741. MuPDF und unabhängig librsvg
bestätigen sämtliche Raster- und Komplexitätsgrenzen. Der hellste Punkt liegt
bei etwa 38,7 % der inneren Rechteckbreite.

Die neue L-Ausgabe entsteht in der regulären überwachten CLI und wird als
`validated` gespeichert. M/S sind zusätzliche direkte Raster-Fit-Gegenproben;
für sie wird keine vollständige CLI-Neukonvertierung behauptet. Drei unabhängig
gezeichnete Größen-/Verlaufsfälle bestehen ebenfalls. Die 16 neuen Formtests
enthalten positive und beschädigte Kontrollen. Weitere Prüfungen und die
Grenzen des Gesamttestlaufs stehen in `checks.json`.

```powershell
.venv/Scripts/python.exe -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir .tmp/crossed-gradient-replay --start AC0110_L --end AC0110_L --search-seed 42 --deterministic-order
.venv/Scripts/python.exe -m pytest -q tests/test_crossed_gradient_panel_runtime.py tests/detailtests/test_non_composite_runtime_helpers.py tests/test_diagonal_cross_panel_runtime.py
```

Die lokale Ausgabe liegt unter `cli/converted_svgs/AC0110_L.svg`, der
Bildvergleich unter `comparison.png`. Zusätzlich sind SVG und Messdaten in den
Bestlistensnapshots gespeichert. Die Katalogübersicht aktualisiert die drei
Beschreibungen und die neue L-Ausgabe mit beiden Renderermessungen; andere
Einträge behalten ausdrücklich ihre historischen Messstände.
