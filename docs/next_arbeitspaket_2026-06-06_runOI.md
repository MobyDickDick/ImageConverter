# Nächstes Arbeitspaket – Plan-B AC0922_S Run OI (2026-06-06)

## Ziel

Run OI arbeitet den nächsten Kandidaten der Plan-B-/Perception-Rotation ab:
`AC0922_S.jpg`. Erwartet werden ein kleiner Kreis auf der rechten Bildhälfte
und ein linker horizontaler Anschluss. Neben der realen Re-Konvertierung wird
die im Review ausgewiesene sehr hohe Abweichung überprüft.

## Reale Re-Konvertierung

Der normale Ein-Datei-Pfad wurde mit Timeout-Guard und festem Ein-Iterations-
Budget ausgeführt:

```bash
timeout 180 env \
  PYTHONPATH=vendor/linux-py310/site-packages:. \
  PYENV_VERSION=3.10.20 \
  ICC_MAX_ITERATIONS=1 \
  python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir artifacts/images_to_convert \
  --output-dir /tmp/ic-ac0922-runoi \
  --start AC0922_S \
  --end AC0922_S \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Der Lauf endete mit Exit `0`, schlug jedoch wegen der generischen, noch nicht
fachlich zugeordneten Beschreibung ein einzelnes Rechteck vor. Diese Ausgabe
verliert sowohl den Kreis als auch den linken Anschluss und wurde deshalb als
Semantik- und Topologieregression verworfen.

## Qualitätsentscheidung

Die Review-Evidenz verwies auf einen nicht vorhandenen primären
`converted_svgs`-Pfad und enthielt dadurch einen veralteten Wert. Die direkte
Nachmessung des tatsächlich aufgelösten, committeten Snapshot-SVGs ergibt:

| Ausgabe | `mean_delta2` | `normalized_mse` | Entscheidung |
| --- | ---: | ---: | --- |
| veralteter Review-Eintrag | `64405.492188` | `0.33015759` | korrigiert |
| realer Rechteck-Vorschlag | `7670.863770` | `0.03932264` | verworfen |
| committeter Kreis + linker Anschluss | `5359.111816` | `0.02747206` | akzeptiert |

Das akzeptierte SVG ist nicht nur semantisch vollständig, sondern besitzt auch
den kleinsten Pixelabstand und liegt deutlich unter der Review-Grenze
`0.04594568`. Ein Regressionstest sichert Dimensionen, Pfadauflösung,
Kreis-/Linienstruktur und Qualitätsgrenze.

## Perception-Lerneffekt und Rotation

Die PF8-Frage ist **generalisiert**: Bilddetektion und bestehendes Artefakt
bestätigen `CircleBackground` und `HorizontalRule`. Da der reale generische
Fallback die erkannten Seeds noch nicht in eine bessere Ausgabe überführt,
wird kein schlechteres Artefakt übernommen. `AC0922_S` wurde aus Triage,
PF8-Zielen und Linkage-Report entfernt; verbleibend sind synchron `AC0414_S`,
`AC0130_M` und `AC0130`.

## Abschluss

Run OI ist abgeschlossen: Reallauf ausgeführt, Regression strikt verworfen,
Qualitätsbaseline korrigiert, akzeptierte Semantik abgesichert und Rotation
fortgeschrieben.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0922-S-Reallauf, direkte SVG-Nachmessung, PF8-Linkage und gezielte Regressionstests.
- **Ergebnis:** Akzeptiertes Snapshot-SVG mit `normalized_mse=0.02747206`; Rechteckvorschlag nicht übernommen.
- **Blocker:** Kein Paketblocker; generische unzugeordnete Beschreibungen nutzen Perception-Seeds im Reallauf noch nicht zuverlässig.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0414_S.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
