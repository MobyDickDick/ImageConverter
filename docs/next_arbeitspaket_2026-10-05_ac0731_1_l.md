# Nächstes Arbeitspaket – AC0731_1_L Quadrat mit P (2026-10-05)

Der erste offene Kandidat nach dem Kreis-Dreieck-Pumpen-Recheck ist
abgeschlossen. Die Registrierung nutzt ausschließlich Raster und Beschreibung;
sie enthält keine neue Runtime-Katalogkennung und liest keine Sample-SVGs.

## Ursache und Beschreibungsqualität

Der bisherige aufrechte Quadratpfad erzeugt nur Körper und unteren Griff,
auch wenn die Beschreibung einen Buchstaben verlangt. Die lokale geometrische
Registrierung kann weder das fehlende Textprimitive noch dessen Schriftlage
ergänzen. Zusätzlich baut die Non-Composite-Runtime ihre IR aus der zuvor
kleingeschriebenen Matching-Beschreibung neu auf; dadurch wurde ein explizites
`P` im ersten CLI-Recheck zu `p`.

Die gemeinsame XML-Beschreibung verweist bisher nur auf „AC071“. Sie ist nun
für die sechs roten und grauen Größenvarianten eigenständig und zutreffend:
**„Kelle mit Quadrat oben, mittigem Griff nach unten und Text \"P\" im Quadrat.“**
Farben und Maße bleiben Rasterbefunde. Die Runtime verwendet beim IR-Neuaufbau
die ursprünglichen Beschreibungsfragmente, damit beschriebener Text seine
Groß-/Kleinschreibung behält.

## Allgemeiner Algorithmus

Der vorhandene `UprightSquareKelleGlyph` erhält einen ausdrücklich zitierten
Text aus der Beschreibung. Ohne beschriebenen Text bleibt er unbeschriftet.
Der Renderer übernimmt diesen Text, statt aus der Symbolfamilie ein Label
abzuleiten. Auch gemischte Groß-/Kleinschreibung bleibt erhalten.

`imageCompositeConverterLabeledSquare.py` prüft rechteckige Außenkanten,
annähernd quadratische Proportionen und einen mittig angeschlossenen unteren
Griff. Dominante Innenfarbe, Randfarbe und Grifffarbe stammen aus dem aktuellen
Raster. Eine innenliegende Kontrastkomponente liefert die Textgrenzen;
Randkomponenten werden verworfen. Schriftgröße und Position werden anhand der
tatsächlichen Fontmetriken des Produktionsrenderers vorinitialisiert.

Eine begrenzte Grob-zu-fein-Suche registriert anschließend Körper, Rand- und
Griffbreite sowie Schriftgröße und Lage. Sie hält Quadrat, Griffanschluss,
Textinhalt und Textposition im Körper zusammen. Ein Ergebnis wird nur bei
sinkendem Renderfehler übernommen. Die Suche prüft höchstens `111`
Parameterkandidaten einschließlich dreier Schriftgewichte; sie übernimmt keine Rasterkontur
als Polygonpfad und bettet kein Bild ein.

Der Registrierer ist auf ein aufrechtes Quadrat, einen unteren Griff und
**einen ausdrücklich beschriebenen Einzelbuchstaben** begrenzt. Er behauptet
keine OCR-Erkennung, Mehrwortregistrierung oder Erkennung beliebig gedrehter
beschrifteter Symbole. Mehrstelliger zitierter Text kann gerendert werden,
nutzt aber diesen Registrierer nicht.

## Harte Abnahme am gespeicherten CLI-SVG

Alle Fälle laufen mit fremden Dateinamen, derselben korrigierten Beschreibung,
Seed `0` und `semantic-only`. Der kontrollierte Vorlauf deaktiviert das neue
Textprimitive im aufrechten Quadratpfad und dessen Rasterregistrierung. Alle
übrigen Startprimitive, Perception- und Runtime-Pfade bleiben aktiv.
Bewertet werden ausschließlich gespeicherte End-SVGs nach erneutem Rendern.

| Rolle | mean_delta2 vorher | mean_delta2 nachher | normalized MSE | Edge-Alignment | Masken-IoU | Beide Gates |
|---|---:|---:|---:|---:|---:|---|
| Rotes Ziel L | 4133,376953 | 920,249756 | 0,004717 | 0,964218 | 0,943522 | bestanden |
| Roter Holdout M | 4219,952637 | 1074,288574 | 0,005507 | 0,917997 | 0,927681 | bestanden |
| Roter Holdout S | 3711,045410 | 490,600006 | 0,002515 | 0,948496 | 0,990385 | bestanden |
| Grauer Holdout L | 7803,251465 | 884,010681 | 0,004532 | 0,755320 | 0,842900 | bestanden |
| Grauer Holdout M | 8700,232422 | 441,522858 | 0,002263 | 0,810257 | 0,911215 | bestanden |
| Grauer Holdout S | 19138,140625 | 548,752014 | 0,002813 | 0,798931 | 0,820755 | bestanden |

Alle Pflichtmetriken verbessern sich oder bleiben unverändert. Die Grenzen
des Good-Solution- und Quality-Complexity-Gates bleiben unverändert. Der
Semantikcheck verlangt genau ein gefülltes Quadrat, einen mittig verbundenen
unteren Griff und den exakten beschriebenen Kontrasttext im Körper. Falscher
Text, abgetrennter Griff, falsche Körperproportionen, zusätzliche Primitive
und Transformationen bestehen diese Prüfung nicht. Ein synthetisches perfektes
SVG kalibriert sämtliche Metriken auf ihre Idealwerte.

Der historische Review-Wert `18881,216797` gehört zur alten Sammelausgabe mit
der katalogabhängigen Beschreibung. Er wird nicht mit dem Vorlauf des
korrigierten Vertrags vermischt. JPEG-, Font- und Antialiasing-Restfehler bleiben;
die bestehenden CLI-Restfehlerwarnungen sind weiterhin sichtbar.

## Perception-Lerneffekt: generalisiert

Das Bild bestimmt Geometrie, Farben und Schriftlage, die Beschreibung den
Buchstaben. Ziel und fünf Holdouts übertragen diesen Vertrag auf zwei Farben
und drei Größen. Runtime-Tests sichern Umbenennungsinvarianz, exaktes `P`
trotz kleingeschriebener Matching-Beschreibung und verbieten Sample-SVG-Zugriff
sowie Raster-Embedding. Synthetische blaue und orange Quadrate prüfen zwei
Lagen, doppelte Größe und die beschriebenen Einzelbuchstaben `P`, `M`, `T`.
Fehlender Text, fehlender Griff und Kreisersatz werden nicht übernommen.
Konstante Fehlerwerte dürfen keinen Input mutieren oder einen Fit akzeptieren.

## Belege, Tests und Reproduktion

Manifest, versiegelte Baseline, zwölf eingefrorene SVGs, CLI-Logs, Quell- und
Artefakthashes liegen unter `artifacts/evaluation/labeled_square_recheck_v1/`.
Zwei unabhängige CLI-Läufe in frischen Ordnern reproduzieren sämtliche
SVG-Bytes und Gateentscheidungen exakt. Der Abnahmebeleg heißt
`report_2026-10-05.json`; `baseline.json` enthält den versiegelten Vorlauf.

Abnahme: **283 fokussierte Tests ohne Skips/Warnungen** und **1509 bestandene
Tests mit 29 bestehenden Windows-Skips im vollständigen Defaultprofil**,
dokumentiert in `tests_2026-10-05.log`. Die Skips betreffen die unter Windows
ausgeschlossenen POSIX-Shell-Integrationstests. `compileall` für
`src`, `tests` und `tools`, CLI-Help-Smoke und Runtime-ID-Nullprüfung sind grün.
Die bereits dokumentierte defekte lokale `.venv` wurde mit isoliertem Python
und kompatiblen temporären Abhängigkeiten umgangen. Für Test-Unterprozesse
lädt der bestehende temporäre Bootstrap diese Abhängigkeiten ebenfalls vor;
die Projektumgebung bleibt unverändert. Toolchain: CPython `3.12.14`, NumPy
`2.5.3`, OpenCV `4.14.0`, PyMuPDF `1.26.7`.

In einer funktionierenden Umgebung mit `requirements-dev.txt`:

```bash
python -m tools.run_labeled_square_recheck \
  artifacts/evaluation/labeled_square_recheck_v1/manifest.json \
  --output-dir .tmp/labeled-square-reproduction
python -m tools.evaluate_labeled_square_recheck \
  artifacts/evaluation/labeled_square_recheck_v1/manifest.json \
  --output .tmp/labeled-square-gates.json
python -m tools.review_conversion_quality \
  --output-dir .tmp/labeled-square-full-review \
  --exclude AC0554_2_L --exclude AC0713_1_S --exclude DLG0010_1 \
  --exclude AC0724_1_S --exclude AC0252_1 --exclude AC0252 --exclude AC0252_2 \
  --exclude AC0731_1_L --exclude AC0731_1_M --exclude AC0731_1_S \
  --exclude AC0731_L --exclude AC0731_M --exclude AC0731_S
python -m compileall src tests tools
python -m pytest -q
python -m src.imageCompositeConverter --help
python -m tools.check_no_new_image_id_hardcoding
```

Der erneuerte Review umfasst `688` renderbare Paare. Die separat belegten
Gate-Passes sind aus der Kandidatenauswahl ausgeschlossen, weil die historische
Sammelausgabe weiterhin alte SVGs enthält. Die auf fünf offene Einträge
aufgefüllte Rotation geht mit **`GE1003_M`** weiter, gefolgt von `AC0404_1_L`,
`GE9011_6M`, `AC0404_1_S` und `GE0281`.
