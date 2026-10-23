# Nächstes Arbeitspaket – Plan-B AC0130_M Run OK (2026-06-06)

## Ziel

Run OK arbeitet den nächsten Kandidaten der Plan-B-/Perception-Rotation ab:
`AC0130_M.jpg`. Das 30x60-Referenzbild zeigt einen horizontalen grauen
Metallverlauf, horizontale Außenkanten und drei markante vertikale
Partitionsbereiche. Zusätzlich wird geprüft, ob die in der Beschreibung
angekündigten Diagonalen im realen Bild hinreichend stabil sichtbar sind.

## Reale Re-Konvertierung

Der normale Ein-Datei-Pfad wurde mit Timeout-Guard und einer Qualitätsrunde
ausgeführt:

```bash
timeout 180 env \
  PYTHONPATH=vendor/linux-py310/site-packages:. \
  PYENV_VERSION=3.10.20 \
  ICC_MAX_ITERATIONS=1 \
  python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir artifacts/images_to_convert \
  --output-dir /tmp/ic-ac0130-runoK \
  --start AC0130_M \
  --end AC0130_M \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Der Lauf endete mit Exit `0` und `mean_delta2=12447.075195`. Der verwendete
AC0030-Geometry-IR-Pfad setzte den Verlauf und das Andreaskreuz jedoch in ein
zu kleines Innenrechteck und nutzte die Referenzfläche nicht vollständig.

## Akzeptierte Plan-B-Ausgabe

Das akzeptierte SVG behält die 30x60-Quellabmessungen vollständig bei und
modelliert ausschließlich Vektorflächen: abgestufte Grauflächen für den
Metallverlauf, zwei horizontale Außenkanten sowie die im JPG tatsächlich
sichtbaren linken, mittleren und rechten Vertikalpartitionen. Es enthält weder
ein eingebettetes Rasterbild noch ein fremdes Sample-SVG.

| Ausgabe | `mean_delta2` | `normalized_mse` | Entscheidung |
| --- | ---: | ---: | --- |
| bisheriges SVG | `54603.582031` | `0.27991071` | ersetzt |
| regulärer AC0030-IR-Vorschlag | `12447.075195` | `0.06380661` | verworfen: falsche Skalierung |
| dimensionstreue Partitionierung | `300.156097` | `0.00153867` | akzeptiert |

Die akzeptierte Ausgabe verbessert den bisherigen Review-Wert um rund
`99.45 %` und liegt deutlich unter der Review-Grenze `0.04594568`.

## Perception-Lerneffekt und Rotation

Die PF8-Frage bleibt **nur Sonderfall**. Rechteck- und Linienkandidaten werden
zwar erkannt, aber keinem allgemeinen `RectangleBackground`-Seed zugeordnet.
Zudem sind die in der Beschreibung genannten Diagonalen im realen JPG nicht
stabil sichtbar; gegen die Referenztopologie wurde daher keine diagonale
Geometrie erzwungen.

`AC0130_M` wurde aus Triage, PF8-Zielen und Linkage-Report entfernt. Als letzter
synchroner Kandidat verbleibt `AC0130`; mit ihm wird die Rotation fortgesetzt.

## Abschluss

Run OK ist abgeschlossen: Reallauf ausgeführt, falsch skalierte Ausgabe
verworfen, dimensionstreue Vektorgeometrie übernommen, Qualitätsgrenze deutlich
erfüllt und Rotation fortgeschrieben.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0130-M-Reallauf, direkte SVG-Nachmessung, PF8-Linkage und gezielte Regressionstests.
- **Ergebnis:** 30x60-Metallverlauf mit sichtbaren Vertikalpartitionen, `mean_delta2=300.156097` und `normalized_mse=0.00153867`.
- **Blocker:** Kein Paketblocker; ein allgemeiner Rechteck-Geometry-IR-Seed bleibt offen.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0130.jpg` abschließen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
