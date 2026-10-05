# Nächstes Arbeitspaket – AC0252_1 Kreis-Dreieck-Pumpe (2026-10-05)

Der erste offene Kandidat nach dem diagonalen Quadrat-Kellen-Recheck ist
abgeschlossen. Die Umsetzung wurde am 2026-10-04 begonnen und am 2026-10-05
auf `codex/ac0252-plan-b` abgenommen. Der Konverter verwendet ausschließlich
Raster und Beschreibung, ohne neue Runtime-Katalogkennung, Sample-SVGs oder
gespeicherte fallspezifische Form-/Farbparameter.

## Ursache und Beschreibungsqualität

Der alte Pumpen-IR startet mit roten Farben und einem aufrechten Dreieck.
Die vorhandene lokale Registrierung kann weder die Dreieckspunkte noch die
Farben aus dem Bild ermitteln. Außerdem fehlt `PumpTriangleGlyph` in der
semantischen Runtime-Auswahl; zusätzliche Perception-Seeds können deshalb
die beschriebene Kreis-Dreieck-Struktur verdrängen.

Die gemeinsame XML nennt auch das rote und grüne Raster grau, beschreibt eine
Linksdrehung und erwähnt einen Griff. Sichtbar sind in allen drei Rastern
ein Kreis und ein nach rechts zeigendes Dreieck ohne Griff. Die XML ist nun
katalogfrei und für alle drei Varianten zutreffend:
**„Pumpensymbol: Kreis mit einem gefüllten Dreieck, dessen Spitze nach rechts zeigt.“**
Farben und Maße bestimmt das Raster. Die Abnahme bestätigt diesen korrigierten
Vertrag; sie bestätigt weder die früheren Farbangaben noch eine Linksdrehung.

## Allgemeiner Algorithmus

`imageCompositeConverterPump.py` prüft eine annähernd kreisförmige Außenkontur
und segmentiert im inneren Kreisbereich deterministisch zwei kontrastreiche
Farben. Genau eine ausreichend große und belegte Dreieckregion muss entstehen.
Kreiszentrum, Radius, Dreieckspunkte, Füllfarben und Randfarbe kommen aus dem
aktuellen Bild. Ein begrenzter Grob-zu-fein-Rendervergleich registriert danach
Geometrie, Randbreite und Farben. Die Runtime übernimmt das Ergebnis nur bei
sinkendem Fehler und schützt den Pumpenvertrag vor generischen Badge-Seeds.

Explizite absolute Spitzenrichtungen sind harte Constraints. Beschriebener
Text, Griffe, Anschlüsse und Verläufe schließen den vereinfachten Detektor aus.
Eine historische relative Drehungsangabe ohne eindeutige Ausgangspose wird
nicht als absolute Richtung interpretiert. Der Pfad rekonstruiert einen Kreis
und ein gefülltes Dreieck auf hellem Hintergrund; er behauptet keine Erkennung
allgemeiner Pumpendiagramme, dünner Pfeile oder zusätzlicher Beschriftungen.

## Harte Abnahme am gespeicherten CLI-SVG

Der echte `semantic-only`-CLI-Recheck verwendet fremde Dateinamen, die gleiche
korrigierte Beschreibung und Seed `0`. Der Vorlauf deaktiviert ausschließlich
die neue Rasterregistrierung und die semantische Pumpenpräferenz. Die alten
Startprimitive, Perception und übrigen Runtime-Pfade bleiben aktiv. Gemessen
werden die auf Platte gespeicherten SVGs nach erneutem Rendern.

| Rolle | mean_delta2 vorher | mean_delta2 nachher | normalized MSE | Edge-Alignment | Masken-IoU | Beide Gates |
|---|---:|---:|---:|---:|---:|---|
| Rotes Ziel | 7316,579590 | 458,776276 | 0,002352 | 0,939825 | 0,943715 | bestanden |
| Grüner Holdout | 7455,887695 | 394,592102 | 0,002023 | 0,906620 | 0,930582 | bestanden |
| Grauer Holdout | 7285,255859 | 328,445374 | 0,001684 | 0,950264 | 0,906921 | bestanden |

Alle Pflichtmetriken verbessern sich oder bleiben unverändert. Die
Good-Solution-/Quality-Complexity-Grenzen sind unverändert. Die Semantikprüfung
verlangt genau eine gefüllte Kreisellipse und ein kontrastierendes, enthaltenes,
nach rechts zeigendes Dreieck. Zusätzliche Text-/Raster-/Pfadprimitive und
Transformationen werden verworfen. Ein perfektes synthetisches SVG kalibriert
die Metriken auf ihre Idealwerte; falsche Richtung, Rechteckersatz und fehlende
Containment-Geometrie fallen durch. JPEG-/Antialiasing-Restfehler bleiben;
die Abnahme behauptet keine pixelidentische Rekonstruktion.

Der historische Review-Wert `20853,748047` gehört zum alten Sammel-SVG und
zur alten Beschreibung. Er wird nicht mit dem deterministischen Vorlauf des
korrigierten Vertrags vermischt.

## Perception-Lerneffekt: generalisiert

Der Rasterbefund ersetzt feste Farbannahmen und die aufrechte Dreieckpose.
Ziel sowie grüne und graue Holdouts funktionieren ohne Katalogkennung. Tests
sichern Umbenennungsinvarianz und verbieten Sample-SVG-/Raster-Embedding-Zugriff.
Synthetische blaue und orange Körper mit cremefarbenem Dreieck prüfen andere
Lage, doppelte Größe und alle vier Spitzenrichtungen. Kreise ohne Dreieck,
rechteckige und runde Innenregionen sowie widersprechende Richtungen werden
nicht als passender Dreieckbefund übernommen.

## Belege, Tests und Reproduktion

Manifest, versiegelte Baseline, sechs eingefrorene SVGs, CLI-Logs und Hashes
liegen unter `artifacts/evaluation/pump_recheck_v1/`. Drei unabhängige CLI-Läufe
in frischen Ausgabeordnern reproduzieren sämtliche SVG-Bytes und Gate-Records
exakt. Der Report heißt `report_2026-10-04.json`; der vollständige Abschlusslog
vom Folgetag heißt `tests_2026-10-05.log`.

Abnahme: **267 fokussierte Tests ohne Skips/Warnungen** sowie **1466 bestandene
Tests und 29 bestehende Skips im vollständigen Defaultprofil**. `compileall`,
CLI-Help-Smoke und Runtime-ID-Nullprüfung sind grün. Die Skips stammen aus den
bereits unter Windows ausgeschlossenen POSIX-Shell-Integrationstests. Die defekte lokale
`.venv` wurde für die Prüfung durch isolierten Python-Start und vorgeladene,
kompatible temporäre Abhängigkeiten umgangen; die Projektumgebung bleibt
unverändert. Toolchain: CPython `3.12.14`, NumPy `2.5.3`, OpenCV `4.14.0`,
PyMuPDF `1.26.7`.

In einer funktionierenden Umgebung mit `requirements-dev.txt`:

```bash
python -m tools.run_pump_recheck \
  artifacts/evaluation/pump_recheck_v1/manifest.json \
  --output-dir .tmp/pump-reproduction
python -m tools.evaluate_pump_recheck \
  artifacts/evaluation/pump_recheck_v1/manifest.json \
  --output .tmp/pump-gates.json
python -m tools.review_conversion_quality \
  --output-dir .tmp/pump-full-review \
  --exclude AC0554_2_L --exclude AC0713_1_S --exclude DLG0010_1 \
  --exclude AC0724_1_S --exclude AC0252_1 --exclude AC0252 --exclude AC0252_2
python -m compileall src tests
python -m pytest -q
python -m src.imageCompositeConverter --help
python -m tools.check_no_new_image_id_hardcoding
```

Der erneuerte Gesamt-Review umfasst `688` renderbare Paare. Die separat
belegten Gate-Passes sind aus der aktiven Kandidatenauswahl ausgeschlossen,
weil die historische Sammelausgabe weiterhin deren alte SVGs enthält.
Die auf fünf offene Einträge aufgefüllte Rotation geht mit **`AC0731_1_L`**
weiter, gefolgt von `GE1003_M`, `AC0404_1_L`, `GE9011_6M` und `AC0404_1_S`.
