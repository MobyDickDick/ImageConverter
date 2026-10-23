# Nächstes Arbeitspaket – DLG0010_1 verschachtelte Rechteckflächen (2026-10-04)

Nach der Quadrat-Kellen-Abnahme ist der nächste aktive Plan-B-Kandidat
`DLG0010_1` abgearbeitet. Der allgemeine Rasterregistrierer erhält ausschließlich
Bild und Beschreibung. Er enthält keine Katalogkennung, Sample-Auswahl oder
gespeicherten Form-/Farbparameter.

## Ursache und Algorithmus

Der alte Panelpfad nimmt eine gleichmäßige Rahmenbreite an. Beim 90×25-Raster
überdeckt er damit das breite rechte Außenfeld; der historische Sammelreview
meldete `mean_delta2=23882.488281`. Ein frischer deterministischer CLI-Vorlauf
reproduziert den Strukturfehler mit `28492.753906`. Diese Werte stammen aus
unterschiedlichen gespeicherten SVGs und werden nicht vermischt.

`imageCompositeConverterNestedPanel.py` erkennt bis zu drei dominante
Farbbereiche, sucht eine große, eingeschlossene rechteckige Komponente und
prüft deren Füllgrad und Farbkonstanz. Das Raster bestimmt Innenlage,
Ausdehnung und beide Farben. Ein Übergangsband wird beim Außenfarbsampling
ausgenommen, damit JPEG-Artefakte nicht als weitere Fläche gelten. Erst nach
dieser Topologieprüfung werden Grenzen und Eckradien durch Rendervergleich
grob zu fein registriert. Der Non-Composite-Pfad vergleicht dieses Ergebnis
mit den bestehenden Panelhypothesen und wählt es nur bei besserem Pixelfehler.
Beschriebene Glyphen, Linien und Verläufe sowie größere Löcher in der Fläche
schließen diesen vereinfachten Pfad aus.

## Beschreibungsvertrag und Abnahme

Die alte XML beschreibt auch das rote Raster als „hellgraues Quadrat“ und
verweist auf `BackBottom`. Das ist kein zutreffender Zwei-Quellen-Vertrag.
Die isolierte Abnahme verwendet deshalb für beide Bilder die katalogfreie
Beschreibung **„Rechteckfläche mit heller rechteckiger Innenfläche.“** Farben
und Maße werden aus dem Bild bestimmt. Der Gate-Pass bestätigt diesen
beobachtbaren Vertrag; er bestätigt nicht die falsche Farbangabe der XML.
Der normale Lauf mit der alten XML erhält ebenfalls die Rasterstruktur, die
XML-Korrektur selbst bleibt als Datenqualitätsfolge dokumentiert.

Der echte `semantic-only`-CLI-Aufruf nutzt die fremden Dateinamen `pilot_panel`
und `renamed_holdout`. Der Vorlauf ist eine Ablation desselben CLI-Pfads mit
deaktiviertem neuen Detektor. Seed, Beschreibungen und Raster bleiben gleich.
Gemessen werden die auf Platte gespeicherten SVGs nach erneutem Rendern,
nicht die Preview und nicht nur der Prozess-Exit.

| Rolle | mean_delta2 vorher | mean_delta2 nachher | normalized MSE | Edge-Alignment | Masken-IoU | Beide Gates |
|---|---:|---:|---:|---:|---:|---|
| Rotes Ziel | 28492,753906 | 468,700897 | 0,002403 | 0,903612 | 1,000000 | bestanden |
| Grauer Holdout | 878,619141 | 48,554668 | 0,000249 | 0,731912 | 0,989738 | bestanden |

Die unveränderten Good-Solution-/Quality-Complexity-Grenzen gelten für beide
Fälle. Alle Pflichtmetriken verbessern sich oder bleiben unverändert. Die
Semantikprüfung kontrolliert zwei verschieden gefüllte, vollständig
ineinanderliegende Rechtecke und verwirft zusätzliche Raster-/Text-/Kreis-
Primitive und Transformationen. Die Maskenmessung trennt den hellen Einsatz
vom dunkleren Außenfeld mit einer aus dem Input bestimmten Luminanzgrenze;
dieselbe Grenze gilt für Vorher und Nachher. Ein synthetisches perfektes SVG
kalibriert alle Metriken auf ihre Idealwerte; fehlende Innenflächen und falsche
Containment-Geometrie schlagen fehl.

**Restgrenzen:** Der graue Holdout liegt mit seiner Kantenmetrik nur knapp über
`0.72`. Beide CLI-Läufe melden weiterhin konzentrierte Restfehler; der graue
Fall landet wegen der historischen globalen Schwelle zudem unter
`converted_svg_failed`. Das wird nicht verborgen. Der hier verwendete
versionierte Gate-Vertrag bewertet das gespeicherte SVG unabhängig davon.
Der neue Detektor ist für zwei annähernd flache Farbflächen gedacht und
behauptet keine Rekonstruktion allgemeiner mehrschichtiger Panels.

## Perception-Lerneffekt: generalisiert

Der neue Rasterbefund ersetzt die Annahme einer festen Rahmenbreite durch
zwei gemessene Rechteckregionen. Ziel und grauer Holdout funktionieren bei
Umbenennung ohne Sample-Zugriff. Synthetische Tests übertragen denselben Pfad
auf eine blaue Außenfläche, einen andersfarbigen Einsatz, geänderte Position
und doppelte Größe. Beschriebener Text oder größere Löcher werden nicht
wegoptimiert.

## Reproduktion und Sicherung

Manifest, versiegelte Baseline, SVG-Hashes und Report:
`artifacts/evaluation/nested_panel_recheck_v1/`. Toolchain: CPython `3.12.14`,
NumPy `2.5.3`, OpenCV `4.14.0`, PyMuPDF `1.26.7`. Die defekte lokale `.venv`
wurde mit isoliertem Python-Start und den vorhandenen temporären Abhängigkeiten
umgangen; die Projektumgebung wurde nicht verändert.

In einer funktionierenden Umgebung mit `requirements-dev.txt`:

```bash
python -m tools.run_nested_panel_recheck \
  artifacts/evaluation/nested_panel_recheck_v1/manifest.json \
  --output-dir .tmp/nested-panel-reproduction
python -m tools.evaluate_nested_panel_recheck \
  artifacts/evaluation/nested_panel_recheck_v1/manifest.json \
  --output .tmp/nested-panel-gates.json
python -m tools.review_conversion_quality \
  --output-dir .tmp/nested-panel-full-review \
  --exclude AC0554_2_L --exclude AC0713_1_S --exclude DLG0010_1
python -m pytest -q -p no:cacheprovider --basetemp .tmp/pytest-nested \
  tests/test_nested_panel_runtime.py tests/test_nested_panel_quality_gate.py \
  tests/detailtests/test_non_composite_runtime_helpers.py \
  tests/detailtests/test_geometry_ir_helpers.py \
  tests/detailtests/test_description_contract_helpers.py \
  tests/detailtests/test_semantic_family_rules_helpers.py \
  tests/test_no_new_image_id_hardcoding.py
```

Abnahme: `222 passed`, ohne Skips oder Warnings. Der separate CLI-Repro erzeugt
alle vier eingefrorenen SVG-Hashes exakt wieder. Die Runtime-ID-Nullprüfung
ist grün. Der erneuerte Gesamt-Review umfasst `688` renderbare Paare und
schließt die drei separat belegten Gate-Passes aus der aktiven Liste aus,
weil die historische Sammelausgabe weiterhin deren alte SVGs enthält.
Die Rotation wird auf fünf offene Kandidaten aufgefüllt und geht mit
`AC0724_1_S` weiter.
