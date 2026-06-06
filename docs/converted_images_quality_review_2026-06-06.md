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
