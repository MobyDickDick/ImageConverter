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
