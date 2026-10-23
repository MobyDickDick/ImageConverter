# Nächstes Arbeitspaket – AC0724_1_S diagonal gespiegelte Quadrat-Kelle (2026-10-04)

Der nach dem Rechteckflächen-Recheck dokumentierte Plan-B-Kandidat
`AC0724_1_S` ist abgeschlossen. Der echte `semantic-only`-CLI-Lauf verwendet
Bild und die bestehende Beschreibung mit entfernter Katalogreferenz, einen
festen Seed und fremde Dateinamen. Es gibt keine neue Runtime-Katalogkennung,
keinen Zugriff auf Sample-SVGs und keine gespeicherten fallspezifischen
Formkoordinaten als Runtime-Eingabe.

## Ursache und Änderung

Der Parser schloss gespiegelte Quadrat-Kellen aus dem aufrechten Pfad aus,
erkannte aber die Hauptdiagonalspiegelung nicht. Die XML-Erwähnung einer
Kreis-Symmetrieachse führte so zum falschen Kreis-/Rechteck-Ersatz. Die neue
`MainDiagonalMirroredSquareKelleGlyph` entsteht durch Vertauschen der
normalisierten Achsen der bestehenden aufrechten Quadrat-/Griff-Topologie.
Damit liegen Quadrat und Griff links beziehungsweise rechts. Die beiden
Runtime-Kind-Sets und der Schutz vor der Kreis-Badge-Heuristik enthalten den
neuen Typ. Die bestehende Rasterregistrierung passt Lage, Größe und Kontur
anschließend an das Eingabebild an.

Die erste reine Topologiekorrektur erreichte beim kleinen Ziel bereits
`mean_delta2=3077.922607`, verfehlte das Kanten-Gate aber knapp
(`edge_alignment=0.714524`, Grenze `0.72`). Beide größeren Holdouts bestanden.
Die noch fehlende helle Innenmarkierung wurde daher vor weiterer
Feinregistrierung als eigener Rasterbefund ergänzt.

`imageCompositeConverterInteriorMark.py` prüft eine kontrastreiche,
eingeschlossene Komponente im registrierten Quadratkörper. Ein zusammenhängender
breiter oberer Balken und ein schmalerer, zentrierter unterer Stiel müssen ein
einfaches orthogonales Profil bilden. Nur bei ausreichender Belegung wird ein
geschlossener Pfad mit acht Ecken erzeugt. Grenzen und Farbe kommen aus diesem
Bild; ein begrenzter Grob-zu-fein-Rendervergleich übernimmt den Pfad nur bei
sinkendem Pixelfehler. Explizit ausgeschlossener Text beziehungsweise eine
ausgeschlossene Markierung wird nicht ergänzt.

Der Parser setzt **kein T-Label** voraus. Die Innenkontur ist eine geometrische
Beobachtung und keine OCR-Aussage über den nicht in der XML beschriebenen
Buchstaben. Der Detektor ist derzeit nur an die neue Quadrat-Kellen-Topologie
angeschlossen; allgemeine Buchstaben, diagonale Marken und schwach erkennbare
Konturen sind damit nicht abgedeckt. Die vorhandenen Stilwerte der aufrechten
Kelle bleiben Initialisierungswerte, keine neu gespeicherten Sample-Parameter.

## Harte Abnahme

Gemessen werden die gespeicherten CLI-SVGs nach erneutem Rendern. Der Vorlauf
deaktiviert ausschließlich den neuen Spiegelungszweig; der Rest der Runtime,
Raster, Beschreibung, Seed und Toolchain bleiben gleich. Beim Ziel reproduziert
er exakt den bisherigen Review-Wert `22276.960938`.

| Rolle | Größe | mean_delta2 vorher | mean_delta2 nachher | normalized MSE | Edge-Alignment | Masken-IoU | Beide Gates |
|---|---|---:|---:|---:|---:|---:|---|
| Ziel | S | 22276.960938 | 569.914673 | 0.002922 | 0.842189 | 0.985782 | bestanden |
| Holdout | M | 14914.067383 | 424.822845 | 0.002178 | 0.917015 | 0.931579 | bestanden |
| Holdout | L | 14094.021484 | 514.872864 | 0.002639 | 0.894066 | 0.919275 | bestanden |

Alle drei Fälle verbessern Pixel-, Kanten-, Masken- und Semantikmetrik ohne
Regression und bestehen die unveränderten Good-Solution-/Quality-Complexity-
Gates. Die Semantikprüfung verlangt ein annähernd quadratisches, gefülltes
Rechteck mit zentriert angeschlossenem Griff rechts. Eine optionale Innenmarkierung
muss vollständig im Körper liegen und eine geschlossene orthogonale Kontur
mit acht Ecken besitzen. Zusätzliche Kreise, Text, Rasterbilder oder
Transformationen werden verworfen. Ein perfekt gerendertes synthetisches
SVG kalibriert die Metriken auf die Idealwerte; falsche Anschlussseite,
Lücke und ungültige Innenkonturen werden abgelehnt.

**Restfehler:** Alle drei CLI-Läufe melden weiterhin
`upper_quartile_error_pixels_form_large_connected_component`. Diese Warnung
bleibt sichtbar. Der Gate-Pass belegt den versionierten Qualitätsvertrag,
keine pixelidentische Rekonstruktion oder allgemeine Texterkennung.

## Perception-Lerneffekt: generalisiert

Die Spiegelung wird aus der sprachlichen Relation abgeleitet und auf die
vorhandenen Primitive angewendet. Der Innenbefund wird aus diesem Raster
ermittelt. S-/M-/L-Holdouts und Umbenennungsinvarianz sichern denselben
Runtime-Pfad ohne Sample-Zugriff. Synthetische Tests übertragen den
Markierungsdetektor auf einen blauen Körper, eine cremefarbene Markierung,
geänderte Lage und doppelte Größe. Unmarkierte Körper und diagonale
Innenkonturen erzeugen keinen erfundenen Balken-/Stiel-Pfad.

## Belege und Reproduktion

Manifest, eingefrorene Vorher-/Nachher-SVGs, CLI-Logs, SHA256-Provenienz und
versiegelter Baseline-Report liegen in
`artifacts/evaluation/diagonal_square_kelle_recheck_v1/`. Toolchain:
CPython `3.12.14`, NumPy `2.5.3`, OpenCV `4.14.0`, PyMuPDF `1.26.7`.
Die defekte lokale `.venv` wurde mit isoliertem Python-Start und den bereits
vorhandenen temporären Abhängigkeiten umgangen; die Projektumgebung wurde
nicht verändert.

In einer funktionierenden Umgebung mit `requirements-dev.txt` und einem
frischen Ausgabeordner (der Runner lehnt vorhandene CLI-Ausgaben ab):

```bash
python -m tools.run_diagonal_square_kelle_recheck \
  artifacts/evaluation/diagonal_square_kelle_recheck_v1/manifest.json \
  --output-dir .tmp/diagonal-square-reproduction
python -m tools.evaluate_diagonal_square_kelle_recheck \
  artifacts/evaluation/diagonal_square_kelle_recheck_v1/manifest.json \
  --output .tmp/diagonal-square-gates.json
python -m tools.review_conversion_quality \
  --output-dir .tmp/diagonal-square-full-review \
  --exclude AC0554_2_L --exclude AC0713_1_S --exclude DLG0010_1 --exclude AC0724_1_S
python -m pytest -q -p no:cacheprovider --basetemp .tmp/pytest-diagonal \
  tests/test_diagonal_square_kelle_runtime.py \
  tests/detailtests/test_non_composite_runtime_helpers.py \
  tests/detailtests/test_geometry_ir_helpers.py \
  tests/detailtests/test_description_contract_helpers.py \
  tests/detailtests/test_semantic_family_rules_helpers.py \
  tests/test_no_new_image_id_hardcoding.py
```

Zwei unabhängige CLI-Wiederholungen in frischen Ausgabeordnern reproduzieren
alle sechs SVG-Hashes und sämtliche Gate-Records exakt. Ältere Ergebnisse
aus bereits benutzten Recheck-Verzeichnissen werden nicht als Baseline
übernommen; die eingefrorenen Belege stammen aus dem frischen Lauf.

Abnahme: `230 passed`, ohne Skips oder Warnings. Die Runtime-ID-Nullprüfung
ist grün. Der Gesamt-Review umfasst erneut `688` renderbare Paare. Die vier
separat belegten Gate-Passes werden aus der aktiven Liste ausgeschlossen,
weil die historische Sammelausgabe weiterhin deren alte SVGs enthält.
Die fünf offenen Kandidaten beginnen jetzt mit **`AC0252_1`**.
