# Arbeitspaket – Kreis mit schrägen Linien und Spirale (2026-10-15)

Branch: `codex/ac0421-quality-2026-10-15`, Basis `d8c4ba0e6`.
`AC0421_1_S` ist der nach b_heating1 dokumentierte nächste reguläre Kandidat.
Alle neun Farb-/Größenvarianten bestehen beide unveränderten regulären Gates
ohne Pflichtmetrikregression. Die sechs farbigen JPGs bestehen zusätzlich die
strengeren Plan-B-Pixelgrenzen. Die drei grauen JPGs behalten einen getrennten
offenen IoU-Folgepunkt; ihre strengere Abnahme wird nicht behauptet.

## Quellen und allgemeiner Algorithmus

Die neun bisherigen Beschreibungen enthalten nur unzugeordnete Platzhalter
und einen nicht vorhandenen Griff. Die Raster zeigen eine gefüllte Kreisscheibe,
zwei nach oben konvergierende schräge Linien zwischen Randpunkten und eine
offene, gegen den Uhrzeigersinn nach innen laufende Spirale. Beide XML-Kataloge
beschreiben diese Primitive jetzt eigenständig. Das Quelleninventar hält alle
ursprünglichen Beschreibungen, Rasterhashes und Abmessungen fest.

Die Registrierung regressiert den Kreis und die beiden Geraden aus dem Raster.
Ihre Schnittpunkte mit dem Kreis bestimmen die Linienenden. Eine zirkuläre
Regression schätzt Spiralzentrum und logarithmische Radiusabnahme aus den
verbleibenden kontrastreichen Pixeln. Eine begrenzte Pixelsuche verfeinert
Geometrie, Strichstärken und Farben. Der Startfehler bleibt eine harte
Obergrenze. Die Spirale wird mit höchstens zehn kubischen Hermite-Segmenten
ausgegeben; die Segmentzahl hängt von der Windung ab, nicht von der Auflösung.
Gemessene Pixelkonturen werden nicht als SVG-Punktlisten ausgegeben.

Eine zusätzliche Beschreibungsregel verhindert, dass die explizit beschriebene
Linien-/Spiralszene durch einen voreingestellten Kreis mit Buchstaben ersetzt
wird. Es werden keine Bildkennungen oder gemessenen Bildparameter in der Runtime
gespeichert, Raster eingebettet oder Referenz-SVGs gelesen. Die Registrierung
ist für die geprüften logarithmischen, nach innen laufenden Spiralen mit zwei
konvergierenden Randlinien `generalisiert`. Andere Windungsrichtungen und
Spiraltopologien sind außerhalb dieser Abnahme. Fehlende Primitive, Lücken,
Zusatzmarkierungen, getrennte Objekte und widersprüchliche Texte werden geprüft.

## Nachweis aus gespeicherten CLI-Ergebnissen

Der echte CLI-Vorlauf mit den neun Originalbeschreibungen und neutralen Namen
wurde vor Änderungen an Runtime und Katalog eingefroren. Jede Seite erhält
frische Wegwerfkopien der Eingaben; Quellhashes und fremde SVG-Lesezugriffe
werden geprüft. Die Wiederholung reproduziert alle 18 Vorher-/Nachher-SVGs
bytegenau. Die vollständigen Originalkataloge und echten Bildnamen reproduzieren
dieselben Baselines und alle neun finalen SVGs. Bewertet werden gespeicherte
SVGs nach erneutem Rendern mit dem Produktionsrenderer.

| Variante | Mean-Delta² vorher | Mean-Delta² nachher | Reguläre Gates | Strengere Pixelgates |
|---|---:|---:|---|---|
| AC0421_1_S | 6915.564941 | 281.067505 | bestanden | bestanden |
| AC0421_1_M | 9987.426758 | 209.873337 | bestanden | bestanden |
| AC0421_1_L | 10631.562500 | 154.966873 | bestanden | bestanden |
| AC0421_S | 2795.452393 | 117.915001 | bestanden | IoU offen |
| AC0421_M | 2810.580078 | 185.643326 | bestanden | IoU offen |
| AC0421_L | 2788.918213 | 96.584999 | bestanden | IoU offen |
| AC0421_2_S | 5395.419922 | 220.962494 | bestanden | bestanden |
| AC0421_2_M | 7243.605469 | 121.462219 | bestanden | bestanden |
| AC0421_2_L | 7846.363281 | 108.148125 | bestanden | bestanden |

Null Pflichtmetrikregressionen und null fremde Referenz-SVG-Zugriffe.
Die unabhängige Semantikprüfung kontrolliert Kreis, Randanschlüsse,
Linienkonvergenz, offene Kurve, Drehrichtung und zunehmende innere Krümmung.

Die separate Vorlage verändert Canvas, Lage, Kreis-/Spiralproportionen,
Linienneigungen und Palette. Zwei echte CLI-Läufe mit Seed `20261015`
bestehen jeweils **17/17** Fälle. Eingangshashes, Ausgabehashes, Kennzahlen,
Komplexität und Gateentscheidungen sind identisch. Direkte Rastertests decken
zusätzlich halbe und doppelte Auflösung, andere Paletten und Verschiebungen ab.

Die graue Fläche liegt nahe der unveränderten Plan-B-Vordergrundschwelle:
JPEG-Pixel schwanken um Grauwert 230. Die strengere Vordergrund-IoU beträgt
für S/M/L `0.649231`, `0.721198`, `0.719814`, jeweils unter `0.85`.
Die regulären Gates und alle übrigen strengeren Kennzahlen bestehen.
`AC0421-PB-GREY` bleibt dafür in `docs/open_tasks.md` offen. Weder Quellen
noch Grenzwerte wurden dafür angepasst. Der Recheck-Runner bewertet seinen
Exit-Code anhand beider regulärer Gates; `strict_pixel_gates` im Bericht
weist die zusätzlichen Befunde vollständig aus.

## Bestandsschutz und Folgepaket

Die Erfolgsübersicht enthält **262 Paare**. Alle 253 bisherigen Indexeinträge
bleiben identisch. Die vollständige Archivprüfung in getrennten Prozessen
besteht mit **262/262** erneuten Review-Pässen. Alle 253 bisherigen
Prüfdatensätze und die 22 bekannten älteren Kompatibilitätsabweichungen bleiben
unverändert. Die fokussierte Suite besteht mit **41 Tests**, die
AC08-/AC0100-Smoke-Prüfung mit zwei Tests. Die vollständige Standardsammlung
besteht in vier getrennten Prozessen mit **2.714 Tests und 30 bestehenden
Skips, null Fehlern**. Alle 2.744 gesammelten Testknoten sind nach Abgleich
der JUnit-Berichte genau einmal enthalten. Vollständige Abschlusszahlen,
Archivprüfung und Artefakthashes stehen im maschinenlesbaren Nachweis
`artifacts/evaluation/spiral_disk_recheck_v1/validation_2026-10-15.json`.

Ein früher fokussierter Diagnoselauf enthielt zwei Fehler: Ein kleines
getrenntes Zusatzobjekt fiel unter die Flächentoleranz, und ein Test ersetzte
wegen Groß-/Kleinschreibung keinen Beschreibungstext. Die allgemeine
Fremdobjekt-Toleranz und die Testmutation sind korrigiert; der finale Lauf
besteht vollständig. Der frühere Log bleibt als Diagnose erhalten.

Der erste ungeteilte Standardlauf lieferte nach 1.800 geschriebenen
Testergebnissen keinen weiteren Fortschritt und wurde ohne Abschlussurteil
beendet. Die gepufferte Ausgabe erlaubt keine sichere Aussage zum exakten
Haltepunkt; dieser Versuch zählt nicht als bestandene Abnahme. Die vollständige
Sammlung wurde deshalb in vier frischen Pytest-Prozessen geprüft. Auswahlplan,
Einzelprotokolle und JUnit-Berichte halten die vollständige Abdeckung fest;
die Ursache des Stillstands wird durch dieses Paket nicht als behoben erklärt.

Der frische Review umfasst 1.000 Einträge und 993 renderbare Paare.
Alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Bestehende Ausschlüsse werden fortgeschrieben; ausschließlich die neun regulär
abgenommenen Varianten werden zusätzlich ausgeschlossen. Es folgen **`GE0306`**,
`GE0346`, `AC0850_L`, `GE0017` und `GE0001_L`. Bestehende offene Aufgaben
bleiben erhalten.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_spiral_disk_recheck artifacts/evaluation/spiral_disk_recheck_v1/manifest.json --output-dir .tmp/spiral-reproduce
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/spiral-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/spiral_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/spiral_disk_recheck_v1/independent.txt --seed 20261015 --output-dir .tmp/spiral-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/spiral-archive-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/spiral-tests-reproduce
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/spiral-standard-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_conversion_regression_smoke.py --basetemp .tmp/spiral-smoke-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse. Das Paket versioniert
Manifest, echte Baselines, finale Vektoren, Quelleninventar, Gateberichte,
unabhängige Vorlage und kompakte Belege beider Plan-B-Läufe. Vollständige
Unterprozessartefakte und frühe Diagnosen bleiben unter `.tmp/spiral-*` erhalten.
