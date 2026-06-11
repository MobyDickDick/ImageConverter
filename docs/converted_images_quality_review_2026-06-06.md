# Qualitätsreview und Plan-B-Triage – 2026-06-06 (Run OG)

## Ziel

Nach Abschluss der AC08-Weak-Family-Rotation wurde die Qualitätsauswertung
aktualisiert und eine neue, auf fünf Einträge begrenzte Plan-B-/PF8-Rotation
kuratiert. Der frühere Inline-Prüfcode ist nun ein wiederholbares Tool.

## Reproduzierbarer Lauf

```bash
PYENV_VERSION=3.10.20 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python tools/review_conversion_quality.py
```

Das Tool prüft zwei Quellen:

1. alle 48 Varianten aus `successed_conversions.txt`,
2. alle 131 Varianten des vorhandenen `*_diff.png`-Inventars.

Originale und SVGs werden über die dokumentierten Konvertierungs-, Snapshot-
und Satisfactory-Pfade aufgelöst. Jedes SVG wird auf die Originalgröße gerendert;
pro Paar werden `mean_delta2` und
`normalized_mse = mean_delta2 / (3 * 255²)` geschrieben.

## Ergebnis

| Metrik | Wert |
| --- | ---: |
| Erfolgreiche Varianten | `48` |
| Renderbare erfolgreiche Paare | `48` |
| Fehlende/fehlerhafte erfolgreiche Paare | `0` |
| Erfolgreiche Varianten oberhalb `0.04594568` | `1` |
| Varianten im Diff-Inventar | `131` |
| Renderbare Diff-Paare | `121` |
| Kuratierte Plan-B-Kandidaten | `5` |

`AC0835_L` ist mit `normalized_mse=0.05726039` der einzige weiterhin rote
Eintrag aus der bisherigen Erfolgsliste. Für das Auffüllen werden nur
renderbare Diff-Fälle oberhalb der Grenze, ohne `_sia`-Spezialnamen und mit
maximal `3200` Pixeln Bildfläche zugelassen. Daraus folgen in stabiler
Prioritätsreihenfolge `AC0922_S`, `AC0414_S`, `AC0130_M` und `AC0130`.

Die vollständigen Datensätze stehen in:

- `artifacts/evaluation/conversion_quality_review_v2/conversion_quality_review_v2.json`
- `artifacts/evaluation/conversion_quality_review_v2/conversion_quality_records_v2.csv`
- `artifacts/evaluation/conversion_quality_review_v2/plan_b_candidate_triage_v1.csv`

## PF8-Kopplung

Der PF8-Linkage-Report wurde mit denselben fünf Varianten neu erzeugt. Alle fünf
Bilder wurden ausgewertet; vier Entscheidungen lauten `generalisiert`, eine
(`AC0130_M`) `nur Sonderfall`, keine `noch nicht erkannt`. Damit besitzt jeder
aktive Kandidat vor dem ersten Re-Konvertierungslauf eine explizite
Perception-Frage und Folgeaktion.

## Entscheidung

Die neue Rotation ist freigegeben. Der nächste Kandidat ist `AC0835_L.jpg`:
Zuerst sollen der dominante Kreis als `CircleBackground` und die kurze
`VOC`-Beschriftung als Textsignal genutzt werden; anschließend ist die reale
Konvertierung gegen die aktualisierte Review-Grenze zu prüfen.


## Folgeaktualisierung Run OH

`AC0835_L` wurde im realen semantischen Konverterpfad erneut erzeugt. Das neue
25x25-SVG enthält den dominanten Kreis und horizontalen `VOC`-Text, aber keinen
Connector. `mean_delta2` sinkt von `11170.070312` auf `7629.902344`; daraus
folgt `normalized_mse=0.03911266`, also ein Wert unterhalb der Review-Grenze.
Der Kandidat ist deshalb abgeschlossen und aus der aktiven Triage entfernt.
Die Rotation wird mit `AC0922_S`, `AC0414_S`, `AC0130_M` und `AC0130`
fortgesetzt.


## Folgeaktualisierung Run OI

Die Nachmessung des tatsächlich aufgelösten Snapshot-SVGs für `AC0922_S`
korrigiert den veralteten Triage-Wert von `normalized_mse=0.33015759` auf
`0.02747206` (`mean_delta2=5359.111816`). Das akzeptierte 25x15-SVG enthält
einen Kreis mit linkem Horizontalanschluss und liegt damit unter der
Review-Grenze.

Der reale Ein-Datei-Lauf endete zwar mit Exit `0`, schlug jedoch ein einzelnes
Rechteck mit `normalized_mse=0.03932264` vor. Diese Ausgabe wäre trotz des
formal grünen Pixelwerts eine klare Semantik- und Topologieregression und wurde
daher nicht übernommen. `AC0922_S` ist durch die bestehende bessere Ausgabe und
einen Regressionstest abgeschlossen; die aktive Rotation lautet nun
`AC0414_S`, `AC0130_M`, `AC0130`.

## Folgeaktualisierung Run OJ

`AC0414_S` wurde als 20x20-Kreis mit drei vom linken Kreisrand ausgehenden
Innenlinien und einer rechten vertikalen Innenkante rekonstruiert. Der reguläre
Ein-Datei-Lauf erzeugte stattdessen einen horizontalen Grauverlauf mit kleinem
Pluszeichen; dieser Vorschlag hatte zwar `mean_delta2=3324.787598`, verfehlte
aber die dokumentierte Topologie und wurde verworfen.

Das akzeptierte SVG senkt `mean_delta2` von `62091.609375` auf `703.882507`
und `normalized_mse` von `0.31829609` auf `0.00360827`. Kreis-/Ring-Erkennung
ist damit als `generalisiert` abgeschlossen. `AC0414_S` wurde aus Triage und
PF8-Linkage entfernt; als nächste Kandidaten bleiben synchron `AC0130_M` und
`AC0130`.


## Folgeaktualisierung Run OK

`AC0130_M` wurde im realen Ein-Datei-Pfad erneut konvertiert. Der reguläre
AC0030-Geometry-IR-Vorschlag erreichte `mean_delta2=12447.075195`, setzte das
Rechteck jedoch deutlich zu klein in die 30x60-Fläche. Das akzeptierte SVG
erhält stattdessen die Referenzabmessungen vollständig und bildet den sichtbaren
Metallverlauf, die horizontalen Außenkanten und die drei vertikalen
Partitionsbereiche als reine Vektorflächen ab.

Die Nachmessung sinkt von `mean_delta2=54603.582031` auf `300.156097` und von
`normalized_mse=0.27991071` auf `0.00153867`. Die PF8-Frage bleibt
`nur Sonderfall`: Rechteck und Linien werden erkannt, aber es gibt keinen
allgemeinen `RectangleBackground`-Seed; außerdem zeigt das reale JPG die in der
Beschreibung genannten Diagonalen nicht stabil. `AC0130_M` ist aus Triage und
Linkage entfernt, sodass `AC0130` als letzter Kandidat verbleibt.


## Folgeaktualisierung Run OL

`AC0130` wurde im realen Ein-Datei-Pfad erneut konvertiert. Der reguläre
AC0030-Geometry-IR-Vorschlag erreichte `mean_delta2=9027.247070`, setzte das
Rechteck und Andreaskreuz jedoch deutlich zu klein in die 40x80-Fläche und lag
mit `normalized_mse=0.04627578` knapp über der Review-Grenze.

Das akzeptierte reine Vektor-SVG bildet den horizontalen Metallverlauf, das
fast vollflächige Außenrechteck, beide beschnittenen Diagonalpfade und die zwei
oberen Minuszeichen dimensionstreu ab. Die Nachmessung sinkt vom bisherigen
Review-Wert `mean_delta2=45778.234375` auf `1921.981201` und von
`normalized_mse=0.23466992` auf `0.00985252`. Die PF8-Frage ist
`generalisiert`; `AC0130` ist aus Triage und Linkage entfernt. Damit ist die in
Run OG kuratierte Rotation vollständig abgeschlossen und synchron leer.


## Folgeaktualisierung Run OM (2026-06-07)

Nach Abschluss der bisherigen Rotation wurde der Review ohne manuelle
Kandidatenvorgabe erneut ausgeführt. Alle 48 Erfolgsvarianten sind renderbar;
`AC0820_L` ist mit `normalized_mse=0.05117826` der einzige Eintrag oberhalb der
Review-Grenze `0.04594568`. Im Diff-Inventar sind 120 von 129 Varianten als
Bild-/SVG-Paar renderbar.

Die deterministische Auswahl ergibt `AC0820_L`, `AC0531_1_S`, `AC0502_1_M`,
`AC0551_1_M` und `AC0403_1_M`. Triage, Plan-B-Liste und PF8-Linkage führen
diese fünf Varianten in derselben Reihenfolge. Der Perception-Report bewertet
vier Fragen als `generalisiert`; `AC0551_1_M` bleibt mangels allgemeinem
Rechteck-/HorizontalRule-Seed `nur Sonderfall`.


## Folgeaktualisierung Run OP (2026-06-08)

`AC0820_L` wurde aus der XML-Beschreibung im realen semantischen AC08-Pfad
erneut konvertiert. Das neue 30x30-SVG enthält einen Kreis und getrennt
gerendertes `CO`/tiefgestelltes `2`, aber keinen Connector. `mean_delta2` sinkt
von `9983.599609` auf `7458.403320`; daraus folgt
`normalized_mse=0.03823352`, also ein Wert unterhalb der Review-Grenze.

Der Qualitätsrefresh meldet nun `0/48` erfolgreiche Varianten oberhalb der
Grenze und rotiert auf `AC0531_1_S`, `AC0502_1_M`, `AC0551_1_M`,
`AC0403_1_M` und den neu aufgefüllten Kandidaten `AC0150_2`. Der PF8-Report
führt dieselben fünf Varianten in derselben Reihenfolge.


## Folgeaktualisierung Run OQ (2026-06-08)

`AC0531_1_S` wurde im realen Non-Composite-Pfad erneut konvertiert. Der
allgemeine Element-Fit leitet nun deklarierte Primitive aus der Beschreibung
ab, erfindet also weder eine zweite Diagonale noch Plus-/Minuszeichen, und
schätzt Farbverlauf, gekürzte Diagonale sowie deren RGB-Farbe aus dem Raster.
Das akzeptierte 20x40-SVG enthält genau eine Diagonale und einen Mittelpunkt.

`mean_delta2` sinkt von `30452.529297` auf `4837.790039`,
`normalized_mse` von `0.15610678` auf `0.02479964` und damit unter die
Review-Grenze. Der Kandidat wurde aus Triage und PF8-Linkage entfernt; die
Rotation lautet nun `AC0502_1_M`, `AC0551_1_M`, `AC0403_1_M`, `AC0150_2`
und `AC0253_1`. Der neue Pumpenkandidat wird durch Kreis-/Ring-Erkennung und
einen allgemeinen `CircleBackground`-Seed als `generalisiert` eingestuft.


## Folgeaktualisierung Run OR (2026-06-08)

`AC0502_1_M` wurde im realen Non-Composite-Pfad erneut konvertiert. Der
Element-Fit transformiert die in der Familienbeschreibung genannte Diagonale
bei einer deklarierten 90-Grad-Variante auf die andere Diagonalachse. Das
akzeptierte 60x30-SVG enthält den rastergemessenen roten Verlauf, genau eine
helle Diagonale von oben links nach unten rechts und einen dunklen Mittelpunkt.

`mean_delta2` sinkt von `30301.542969` auf `3126.661621`,
`normalized_mse` von `0.15533278` auf `0.01602799` und damit deutlich unter
die Review-Grenze. `AC0502_1_M` wurde aus Triage und PF8-Linkage entfernt;
die Rotation lautet nun `AC0551_1_M`, `AC0403_1_M`, `AC0150_2`, `AC0253_1`
und `AC0551_2_M`. Die neue AC0551-Frage bleibt mangels allgemeinem
Rechteck-/HorizontalRule-Seed `nur Sonderfall`.


## Folgeaktualisierung Run OT (2026-06-09)

`AC0403_1_M` wurde im realen Non-Composite-Pfad aus der referenzierenden
Familienbeschreibung als semantisches Pumpensymbol re-konvertiert. Das neue
Geometry-IR trennt den dunkleren Kreisgrundkörper vom um 180 Grad gedrehten
Innendreieck; die Rasterregistrierung skaliert die allgemeine Geometrie ohne
variantenspezifische Koordinaten.

`mean_delta2` sinkt von `21687.341797` auf `4297.878906`,
`normalized_mse` von `0.11117438` auf `0.02203193` und damit unter die
Review-Grenze. `AC0403_1_M` wurde aus Triage und PF8-Linkage entfernt; die
Rotation lautet nun `AC0150_2`, `AC0253_1`, `AC0551_2_M`, `AC0733_1_L` und
`AC0733_1_M`.


## Folgeaktualisierung Run OU (2026-06-09)

`AC0150_2` wurde im realen Non-Composite-Pfad erneut konvertiert. Die bereits
allgemeine, beschreibungsgetriebene Chevron-Topologie wird mit einer robusten
RGB-Verlaufsschätzung kombiniert: Der helle Verlaufsstopp stammt aus dem
zentralen Farbbereich und nicht mehr aus einer vom weißen Rahmen oder der
hellen Winkelkontur dominierten Maximalspalte.

`mean_delta2` sinkt von `20470.750000` auf `7988.364258`,
`normalized_mse` von `0.10493784` auf `0.04095022` und damit unter die
Review-Grenze. `AC0150_2` wurde aus Triage und PF8-Linkage entfernt; die
Rotation lautet nun `AC0253_1`, `AC0551_2_M`, `AC0733_1_L`, `AC0733_1_M`
und `AC0722_1_L`. Der neue AC0722-Kandidat ist in der Perception-Auswertung
wegen einer fälschlich priorisierten Kreisdetektion `noch nicht erkannt`.


## Folgeaktualisierung Run OV (2026-06-11)

`AC0253_1` wurde im realen Non-Composite-Pfad aus der AC0251-referenzierenden
Familienbeschreibung erneut konvertiert. Das bereits allgemeine Geometry-IR
trennt Kreisgrundkörper und um 180 Grad gedrehtes Innendreieck; die
Rasterregistrierung passt Farben und Geometrie an die 31x31-Variante an.

`mean_delta2` sinkt von `20431.550781` auf `3327.906250`,
`normalized_mse` von `0.10473690` auf `0.01705962` und damit unter die
Review-Grenze. `AC0253_1` wurde aus Triage und PF8-Linkage entfernt; die
Rotation lautet nun `AC0551_2_M`, `AC0733_1_L`, `AC0733_1_M`,
`AC0722_1_L` und `AC0723_1_S`. Der neue AC0723-Kandidat wird als
`nur Sonderfall` bewertet, weil zwar der Anschluss als Linie erkannt wird,
aber noch kein allgemeiner Rechteck-Seed vorliegt.


## Folgeaktualisierung Run OW (2026-06-11)

`AC0551_2_M` wurde im realen Non-Composite-Pfad erneut konvertiert. Der für
die erste Familienvariante eingeführte allgemeine Chevron-Fit überträgt die
beschriebene Punktfolge Oben-Mitte → Rechts-Mitte → Unten-Mitte ohne neue
Sonderfalllogik auf die zweite Variante. Das akzeptierte 30x60-SVG enthält
genau eine rasterangepasste Winkelkontur und keine erfundenen Diagonalen oder
Glyphen.

`mean_delta2` sinkt von `18425.703125` auf `3294.235596`,
`normalized_mse` von `0.09445446` auf `0.01688702` und damit unter die
Review-Grenze. `AC0551_2_M` wurde aus Triage und PF8-Linkage entfernt; die
Rotation lautet nun `AC0733_1_L`, `AC0733_1_M`, `AC0722_1_L`,
`AC0723_1_S` und `AC0732_1_M`. Der neue Kandidat wird wegen einer
priorisierten Kreisdetektion zunächst als `noch nicht erkannt` eingestuft.


## Folgeaktualisierung Run OX (2026-06-11)

`AC0733_1_L` wurde im realen Non-Composite-Pfad als semantisches
Quadrat-Kellen-Symbol erneut konvertiert. Das neue Geometry-IR trennt den
vertikalen Anschluss, den roten Quadratgrundkörper und den horizontal
bleibenden P-Glyph; die Rasterregistrierung passt Lage und Skalierung an die
25x45-Variante an, ohne den Text zu rotieren.

`mean_delta2` sinkt von `17993.140625` auf `2707.703125`,
`normalized_mse` von `0.09223704` auf `0.01388032` und damit unter die
Review-Grenze. `AC0733_1_L` wurde aus Triage und PF8-Linkage entfernt; die
Rotation lautet nun `AC0733_1_M`, `AC0722_1_L`, `AC0723_1_S`,
`AC0732_1_M` und `AC0732_1_L`. Der neue AC0732-Kandidat bleibt wegen einer
priorisierten Kreisdetektion zunächst `noch nicht erkannt`.


## Folgeaktualisierung Run OY (2026-06-11)

`AC0733_1_M` wurde im realen Non-Composite-Pfad mit demselben semantischen
Quadrat-Kellen-Geometry-IR wie die große Variante erneut konvertiert. Anschluss,
roter Quadratgrundkörper und horizontaler P-Glyph bleiben getrennte Elemente;
die Rasterregistrierung passt ausschließlich größenrelative Lage-, Skalierungs-
und Strichparameter an die 20x35-Variante an.

`mean_delta2` sinkt von `17248.937500` auf `3555.331543`,
`normalized_mse` von `0.08842208` auf `0.01822546` und damit unter die
Review-Grenze. `AC0733_1_M` wurde aus Triage und PF8-Linkage entfernt; die
Rotation lautet nun `AC0722_1_L`, `AC0723_1_S`, `AC0732_1_M`,
`AC0732_1_L` und `AC0254_2`. Der neue AC0254-Kandidat bleibt mangels eines
allgemeinen Rechteck-/Rule-Seeds zunächst `nur Sonderfall`.


## Folgeaktualisierung Run OZ (2026-06-11)

`AC0722_1_L` wurde im realen Non-Composite-Pfad als semantisches
Quadrat-Kellen-Symbol erneut konvertiert. Das neue Geometry-IR trennt den
horizontalen Anschluss, den roten Quadratgrundkörper und den horizontal
bleibenden T-Glyph; alle Koordinaten bleiben größenrelativ.

`mean_delta2` sinkt von `14995.260742` auf `4721.479004`,
`normalized_mse` von `0.07686921` auf `0.02420340` und damit unter die
Review-Grenze. `AC0722_1_L` wurde aus Triage und PF8-Linkage entfernt; die
Rotation lautet nun `AC0723_1_S`, `AC0732_1_M`, `AC0732_1_L`, `AC0254_2`
und `AC0732_1_S`. Der neue AC0732-Kandidat bleibt wegen einer priorisierten
Kreisdetektion zunächst `noch nicht erkannt`.


## Folgeaktualisierung Run PA (2026-06-11)

`AC0723_1_S` wurde im realen Non-Composite-Pfad als vertikal gespiegeltes
Quadrat-Kellen-Symbol erneut konvertiert. Das neue Geometry-IR trennt den oberen
vertikalen Anschluss, den roten Quadratgrundkörper und den horizontal bleibenden
T-Glyph; alle Koordinaten bleiben größenrelativ.

`mean_delta2` sinkt von `14441.021484` auf `2197.709229`,
`normalized_mse` von `0.07402805` auf `0.01126597` und damit unter die
Review-Grenze. `AC0723_1_S` wurde aus Triage und PF8-Linkage entfernt; die
Rotation lautet nun `AC0732_1_M`, `AC0732_1_L`, `AC0254_2`, `AC0732_1_S`
und `AC0701_1_S`. Der neue AC0701-Kandidat ist mangels passender allgemeiner
Rechteck-/Linienkandidaten zunächst `noch nicht erkannt`.
