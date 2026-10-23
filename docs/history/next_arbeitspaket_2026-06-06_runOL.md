# Nächstes Arbeitspaket – Plan-B AC0130 Run OL (2026-06-06)

## Ziel

Run OL schließt die in Run OG kuratierte Plan-B-/Perception-Rotation mit
`AC0130.jpg` ab. Das 40x80-Referenzbild zeigt ein nahezu vollflächiges graues
Kühlelement mit horizontalem Metallverlauf, Außenrechteck, zwei beschnittenen
Diagonalpfaden und zwei kurzen Minuszeichen in der oberen Mitte.

## Reale Re-Konvertierung

Der normale Konverterpfad wurde mit Timeout-Guard und einer Qualitätsrunde
angestoßen:

```bash
timeout 180 env \
  PYTHONPATH=vendor/linux-py310/site-packages:. \
  PYENV_VERSION=3.10.20 \
  ICC_MAX_ITERATIONS=1 \
  python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir artifacts/images_to_convert \
  --output-dir /tmp/ic-ac0130-runOL \
  --start AC0130 \
  --end AC0130 \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Der Lauf endete mit Exit `0` und erzeugte für `AC0130` einen Vorschlag mit
`mean_delta2=9027.247070`. Wie bei `AC0130_M` setzte der reguläre
AC0030-Geometry-IR-Pfad das Rechteck jedoch zu klein in die Referenzfläche; der
Wert liegt mit `normalized_mse=0.04627578` außerdem knapp oberhalb der
Review-Grenze.

## Akzeptierte Plan-B-Ausgabe

Das akzeptierte SVG behält die 40x80-Quellabmessungen bei. Es modelliert den
Metallverlauf durch rendererstabile Vektorstreifen, das fast vollflächige
Außenrechteck, beide an dessen Kanten beschnittenen Diagonalpfade und die zwei
oberen Minuszeichen. Es enthält keine Rastereinbettung und übernimmt kein
fremdes Sample-SVG.

| Ausgabe | `mean_delta2` | `normalized_mse` | Entscheidung |
| --- | ---: | ---: | --- |
| bisheriges SVG | `45778.234375` | `0.23466992` | ersetzt |
| regulärer AC0030-IR-Vorschlag | `9027.247070` | `0.04627578` | verworfen: falsche Skalierung |
| dimensionstreues Kühlelement | `1921.981201` | `0.00985252` | akzeptiert |

Die akzeptierte Ausgabe verbessert den bisherigen Review-Wert um rund
`95.80 %` und liegt deutlich unter der Review-Grenze `0.04594568`.

## Perception-Lerneffekt und Rotation

Die PF8-Frage ist **generalisiert**. Der Detektionsvertrag findet Linien-,
Rechteck-, Kreis- und Ringkandidaten und ordnet einen `CircleBackground`-Seed
als vorinitialisierten Geometry-IR-Hinweis zu. Die akzeptierte Ausgabe nutzt die
fachlich relevanten Außen- und Diagonallinien explizit, ohne aus dem
zusätzlichen Kreissignal eine falsche sichtbare Form abzuleiten.

`AC0130` wurde aus Triage, PF8-Zielen und Linkage-Report entfernt. Damit sind
alle fünf in Run OG kuratierten Kandidaten abgeschlossen und die aktive Rotation
ist synchron leer.

## Abschluss

Run OL ist abgeschlossen: Reallauf ausgeführt, zu klein skalierten Vorschlag
verworfen, dimensionstreue Vektorgeometrie übernommen, Qualitätsgrenze erfüllt
und die aktuelle Plan-B-/Perception-Rotation vollständig beendet.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0130-Reallauf, direkte SVG-Nachmessung, PF8-Linkage und gezielte Regressionstests.
- **Ergebnis:** 40x80-Kühlelement mit `mean_delta2=1921.981201` und `normalized_mse=0.00985252`.
- **Blocker:** Kein Paketblocker; der reguläre AC0030-Pfad skaliert die Referenzgeometrie weiterhin zu klein.
- **Nächster Schritt:** Einen neuen Qualitätsrefresh ausführen und daraus die nächste Plan-B-Rotation kuratieren.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
