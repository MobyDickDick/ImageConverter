# Arbeitspaket Ã¢â‚¬â€œ Quadrat mit rechtem Griff und horizontalem P (2026-10-11)

Branch: `codex/ac0734-quality-2026-10-11`.
Das nÃƒÂ¤chste dokumentierte Ziel `AC0734_1_S` und alle fÃƒÂ¼nf Farb-/GrÃƒÂ¶ÃƒÅ¸en-Holdouts
bestehen beide unverÃƒÂ¤nderten regulÃƒÂ¤ren Gates ohne Pflichtmetrikregression.
Alle sechs JPGs bestehen zusÃƒÂ¤tzlich die strengeren Plan-B-Pixelgrenzen.

## Ursache und allgemeine Korrektur

Die ursprÃƒÂ¼ngliche XML-Beschreibung verwies auf sich selbst und enthielt keine
eigenstÃƒÂ¤ndige Quadrat-/Griffbeschreibung. Beide Kataloge beschreiben jetzt ein
gefÃƒÂ¼lltes Quadrat mit Kontur, mittigem waagerechtem Griff nach rechts und dem
horizontalen Text `P`. MaÃƒÅ¸e und Farben bleiben Rasterbefunde.

Der vorhandene Registrierer fÃƒÂ¼r beschriftete Quadrate ist auf einen unteren
Griff begrenzt. Die neue Richtungsnormalisierung transponiert Quadrat und Griff
fÃƒÂ¼r diese Suche, rendert den Text aber in den ursprÃƒÂ¼nglichen Achsen. Dadurch
bleiben Schrift und GroÃƒÅ¸-/Kleinschreibung horizontal erhalten. Die RÃƒÂ¼ckabbildung
schreibt native SVG-Koordinaten: ein Rechteck, einen Griffpfad und ein Textelement,
ohne Rastereinbettung oder SVG-Transformation. Der explizite Text wird aus der
ursprÃƒÂ¼nglichen Beschreibung ÃƒÂ¼bernommen; es gibt keine neue Runtime-Katalogkennung.

Der kleinste graue Fall wurde zuvor vom Rahmen-Ersatzpfad vereinfacht, bevor die
Textregistrierung lief. Explizit beschriebene Rechtsgriff-/Textmotive werden daher
vor diesem Pfad registriert. Eine zusÃƒÂ¤tzliche KonturprÃƒÂ¼fung beobachtet Randfarben
und verfeinert Rechtecklage und Konturbreite anhand des Renderfehlers; ÃƒÅ“bernahmen
verlangen gleichzeitig sinkenden Optimierungs- und Pixelfehler sowie unverÃƒÂ¤nderte
oder bessere Kanten- und Maskenwerte. Die Suche bleibt auf hÃƒÂ¶chstens 204
Parameterbewertungen begrenzt; Fontmetriken werden zusÃƒÂ¤tzlich gerendert.

Die unabhÃƒÂ¤ngigen Zufallsvarianten deckten eine Beschreibungsmehrdeutigkeit auf:
Eine Verschiebung des ganzen Motivs nach links ist kein linker Griff. Der Parser
unterscheidet solche Lageangaben von ausdrÃƒÂ¼cklich widersprÃƒÂ¼chlichen Griff- und
Drehrichtungen. Vorhandene unbeschriftete Rechtsgriffmotive und historische
Texttopologien behalten ihre bisherigen VertrÃƒÂ¤ge.

## Frische CLI-Abnahme

Vor den Runtime- und KatalogÃƒÂ¤nderungen wurden sechs CLI-Ausgaben mit den echten
Originalbeschreibungen und neutralen Dateinamen eingefroren. Der gemeinsame
Recheck-Runner verwendet Wegwerfkopien, kontrolliert Quellhashes und sperrt
Referenz-SVG-Zugriffe. Sein Rechtsgriff-Vorlauf deaktiviert die neue Registrierung;
die ursprÃƒÂ¼ngliche Beschreibung wÃƒÂ¤hlt sie ohnehin nicht aus. Alle sechs echten
Vorlauf-SVGs bleiben bytegleich.

Die Messung rendert gespeicherte End-SVGs erneut mit dem Produktionsrenderer.
Der unabhÃƒÂ¤ngige Semantikcheck verlangt Quadrat, verbundenen mittigen Rechtsgriff
und den exakten horizontalen Kontrasttext im Quadrat.

| Bild | Mean-DeltaÃ‚Â² vorher | Mean-DeltaÃ‚Â² nachher |
|---|---:|---:|
| AC0734_1_L | 11423.796875 | 622.839111 |
| AC0734_1_M | 12055.801758 | 587.574280 |
| AC0734_1_S | 18331.007812 | 601.298645 |
| AC0734_L | 7437.330566 | 276.005341 |
| AC0734_M | 5429.790039 | 392.935699 |
| AC0734_S | 6959.248047 | 250.087997 |

**6/6 bestehen beide regulÃƒÂ¤ren Gates und sÃƒÂ¤mtliche strengeren Pixelgrenzen;
null Pflichtmetrikregressionen.** Zwei unabhÃƒÂ¤ngige CLI-Abnahmen reproduzieren
alle zwÃƒÂ¶lf Vorher-/Nachher-SVGs und die Gateentscheidungen exakt.
Verbotene Referenz-SVG-Zugriffe: null. Die Restfehlerwarnungen der CLI bleiben
sichtbar. Der historische Sammelwert `12591.893555` fÃƒÂ¼r das Ziel ist keine
frische Originalbeschreibung-Baseline.

## Perception-Lerneffekt: generalisiert

Eine unabhÃƒÂ¤ngig konstruierte blaue Vorlage mit anderer Geometrie besteht mit
Seed `20261011` Original plus 16 Zufallsvarianten ÃƒÂ¼ber die echte CLI (**17/17**).
Ein zweiter Lauf mit demselben Seed reproduziert sÃƒÂ¤mtliche Ausgabehashes und
QualitÃƒÂ¤tsmetriken. Tests prÃƒÂ¼fen andere Farben einschlieÃƒÅ¸lich heller FÃƒÂ¼llung mit
dunklem Text, verschobene Lage, doppelte AuflÃƒÂ¶sung und die expliziten Zeichen
`P`, `M`, `T` und `p`. Umbenennung, fehlender Griff oder Text, Kreisersatz,
abgetrennter Griff, zusÃƒÂ¤tzliche ÃƒÂ¤uÃƒÅ¸ere Objekte, nicht endliche Daten und
fehlendes Rendering sind abgesichert. Der Konverter erhÃƒÂ¤lt nur Raster und Text.

Der Nachweis betrifft die geprÃƒÂ¼fte Quadrat-/Rechtsgriff-/Einzelzeichenstruktur.
OCR, Mehrwortregistrierung und beliebige andere Topologien sind dadurch nicht
belegt. Die handbearbeitete Sammlung unter `artifacts/samples` bleibt unverÃƒÂ¤ndert.

## ErfolgsÃƒÂ¼bersicht, Testvorlagen und nÃƒÂ¤chste Rotation

Die sechs Paare sind mit Beschreibung, Messwerten und Hashes in der separaten
ErfolgsÃƒÂ¼bersicht abgelegt. Sie enthÃƒÂ¤lt jetzt **198** Paare; alle 192 bisherigen
IndexeintrÃƒÂ¤ge bleiben unverÃƒÂ¤ndert.

Der Gesamttestlauf konnte zunÃƒÂ¤chst keine Tests sammeln, weil ÃƒÂ¤ltere PrÃƒÂ¼fungen
noch den entfernten Ordner `artifacts/images_to_convert/samples` voraussetzten.
Sieben historische SVG-/Textdateien aus dem Elterncommit von `e955203aa` liegen
jetzt unverÃƒÂ¤ndert unter `tests/fixtures/plan_b_templates`. Die betroffenen Tests
rasterisieren diese eingefrorenen Vorlagen. Die laufende Handbearbeitung und
kÃƒÂ¼nftige Plan-B-Erweiterungen sind damit unabhÃƒÂ¤ngig von bisherigen Regressionen.
Die Runtime erhÃƒÂ¤lt keinen Zugriff auf diese Vektoren.

Der erneuerte Review enthÃƒÂ¤lt 1.000 EintrÃƒÂ¤ge und 993 renderbare Paare. Alle 48
bisherigen BestenlisteneintrÃƒÂ¤ge bleiben unter der unverÃƒÂ¤nderten Reviewgrenze.
Nach Ausschluss der sechs erledigten Varianten folgt **`GE9021_1M`**, danach
`SE0081`, `GE0039_M`, `GE9022_2M` und `AC0920_L`.
Bekannte GraufÃƒÂ¤lle, ÃƒÂ¤ltere Archivdrift, U-Bogen-StressprÃƒÂ¼fung und die
KatalogquellenprÃƒÂ¼fung bleiben separat offen.

Fokussierte Abnahme: **117 bestandene Tests**. Die zehn schweren
Bestandsschutz-/Conversion-Smoke-/Weak-Family-Tests bestehen ebenfalls,
einschlieÃƒÅ¸lich der 31 geschÃƒÂ¼tzten Varianten. SyntaxprÃƒÂ¼fung fÃƒÂ¼r `src`, `tests`
und `tools`, CLI-Hilfe und Runtime-ID-NullprÃƒÂ¼fung bestehen.
Der vollständige Standardlauf erfasst **2.325 Fälle**: 2.289 bestanden,
30 bestehende Skips und sechs Fehler wegen veralteter Ablagen. Er dauert
12.781,31 Sekunden. Vier AR0030-Vorlagenfälle bestehen nach der Pfadkorrektur
im separaten Nachlauf; die vier Kompaktprüfungen und der Pumpenfall bestehen
ebenfalls. Die native Windows-Meldung `0xc0000008` tritt beim OpenCV-Zugriff
auf den nicht mehr vorhandenen Pumpenpfad auf; mit dem richtigen Pfad besteht
der Fall bei identischen Bildbytes.

Der Gesamtnachweis umfasst damit **2.295 eindeutig bestandene Tests,
30 bestehende Skips und keine ungelösten Fehler**. Es wird kein zweiter
vollständig grüner monolithischer Lauf behauptet. Erstlauf und sämtliche
Nachprüfungen stehen getrennt in `validation_2026-10-11.json`; ausführliche
Logs liegen unter `.tmp/ac0734-*.log`.

## Reproduktion

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_top_stem_square_recheck artifacts/evaluation/right_stem_labeled_square_recheck_v1/manifest.json --output-dir .tmp/right-labeled-square-reproduction
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/right_stem_labeled_square_recheck_v1/independent.svg --description-file artifacts/evaluation/right_stem_labeled_square_recheck_v1/independent.txt --seed 20261011 --output-dir .tmp/right-labeled-square-plan-b --keep-debug-artifacts
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --output-dir .tmp/right-labeled-square-archive
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/right-labeled-square-full
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Jeder CLI- und Archivrecheck benÃƒÂ¶tigt ein frisches Ausgabeverzeichnis.
Manifest, eingefrorene SVGs, Gatebericht, strenge PixelprÃƒÂ¼fung, unabhÃƒÂ¤ngige
Vorlage, kompakter CLI-Plan-B-Bericht, Reproduzierbarkeit, Archiverhaltung und
Review-Aufruf stehen unter `artifacts/evaluation/right_stem_labeled_square_recheck_v1/`.
Der Review lÃƒÂ¤sst sich mit den Argumenten in `review_args.json` wiederholen.
