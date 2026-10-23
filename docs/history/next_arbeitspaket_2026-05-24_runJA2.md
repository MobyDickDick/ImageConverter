# Nächstes Arbeitspaket – 2026-05-24 (runJA2)

## 1) Plan-B-Aufgabe aus neuem Sample ableiten
- Quelle: `artifacts/images_to_convert/samples/AC0030.svg`
- Ziel: Für `AC0030` soll bei nicht-kompositen Fallbacks der Plan-B-Sample-Vergleich greifen, damit kein eingebettetes Raster als Endergebnis bevorzugt wird.

## 2) Einzelprüfung für AC0030.jpg (inkl. Größenvarianten)
- Ausgeführt:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030 --end AC0030`
- Ergebnis:
  - Exit-Code `0`.
  - Für `AC0030.jpg` wurde explizit Plan B über das neue Sample bestätigt:
    - `Plan B Vergleich aktiv: nutze Sample-SVG artifacts/images_to_convert/samples/AC0030.svg (err=175.185, baseline=198.987).`
  - Auch für `AC0030_L.jpg`, `AC0030_S.jpg`, `AC0030_M.jpg` wurde Plan B mit jeweils niedrigerem Sample-Fehler als Baseline genutzt.

## 3) Qualitätsaussage
- Da für `AC0030.jpg` der Sample-Fehler (`err=175.185`) unter der Baseline (`198.987`) liegt und der Lauf erfolgreich endet, ist die Konvertierung mit der geforderten Plan-B-Qualitätslogik für diese Datei aktuell möglich.
