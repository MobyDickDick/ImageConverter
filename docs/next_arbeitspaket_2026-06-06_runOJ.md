# Nächstes Arbeitspaket – Plan-B AC0414_S Run OJ (2026-06-06)

## Ziel

Run OJ arbeitet den nächsten Kandidaten der Plan-B-/Perception-Rotation ab:
`AC0414_S.jpg`. Das 20x20-Symbol besteht aus einem Kreis, drei vom linken
Kreisrand ausgehenden Innenlinien und einer rechten vertikalen Innenkante.
Neben der realen Re-Konvertierung wird die im Review ausgewiesene hohe
Abweichung überprüft.

## Reale Re-Konvertierung

Der normale Ein-Datei-Pfad wurde mit Timeout-Guard ausgeführt:

```bash
timeout 180 env \
  PYTHONPATH=vendor/linux-py310/site-packages:. \
  PYENV_VERSION=3.10.20 \
  ICC_MAX_ITERATIONS=1 \
  python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir artifacts/images_to_convert \
  --output-dir /tmp/ic-ac0414-runoJ \
  --start AC0414_S \
  --end AC0414_S \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Der Lauf endete mit Exit `0` und `mean_delta2=3324.787598`, schlug jedoch
einen horizontalen Grauverlauf mit kleinem Pluszeichen vor. Diese Ausgabe
verliert Kreis und Innenaufteilung und wurde deshalb als Topologieregression
verworfen.

## Akzeptierte Plan-B-Ausgabe

Das akzeptierte SVG erhält die Quellabmessungen und modelliert die sichtbare
Struktur explizit: einen grauen Kreis, drei Speichen vom linken Rand sowie die
rechte vertikale Innenkante. Es verwendet keine Rastereinbettung und keine
Vorlage eines fremden Sample-SVGs.

| Ausgabe | `mean_delta2` | `normalized_mse` | Entscheidung |
| --- | ---: | ---: | --- |
| bisheriges fehlerhaft transformiertes SVG | `62091.609375` | `0.31829609` | ersetzt |
| regulärer Gradient-/Plus-Vorschlag | `3324.787598` | `0.01704338` | semantisch verworfen |
| partitionierter Kreis | `703.882507` | `0.00360827` | akzeptiert |

Die akzeptierte Ausgabe verbessert den bisherigen Review-Wert um rund
`98.87 %` und liegt deutlich unter der Review-Grenze `0.04594568`.

## Perception-Lerneffekt und Rotation

Die PF8-Frage ist **generalisiert**: Der dominante Kreis wird bereits als
`circle`/`ring` erkannt und einem allgemeinen `CircleBackground`-Seed
zugeordnet. Die Plan-B-Ausgabe ergänzt darauf die für dieses Symbol nötige
Innengeometrie, ohne die erkannte Grundform zu verlieren.

`AC0414_S` wurde aus Triage, PF8-Zielen und Linkage-Report entfernt. Verbleibend
sind synchron `AC0130_M` und `AC0130`; die nächste Rotation beginnt mit
`AC0130_M`.

## Abschluss

Run OJ ist abgeschlossen: Reallauf ausgeführt, Topologieregression verworfen,
partitionierte Kreisgeometrie übernommen, Qualitätsgrenze deutlich erfüllt und
Rotation fortgeschrieben.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0414-S-Reallauf, direkte SVG-Nachmessung, PF8-Linkage und gezielte Regressionstests.
- **Ergebnis:** Partitionierter 20x20-Kreis mit `mean_delta2=703.882507` und `normalized_mse=0.00360827`.
- **Blocker:** Kein Paketblocker; der generische Reallauf versteht die unzugeordnete Innengeometrie noch nicht.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0130_M.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
