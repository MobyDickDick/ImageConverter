# Nächstes Arbeitspaket – Plan-B AC0835_L Run OH (2026-06-06)

## Ziel

Run OH arbeitet den ersten Kandidaten der in Run OG kuratierten
Plan-B-/Perception-Rotation vollständig ab: `AC0835_L.jpg`. Der bisher
committete Altbestand war zwar als erfolgreich markiert, zeigte aber nur einen
kleinen Kreis mit falscher Lage, einem unerlaubten Connector und ohne
`VOC`-Beschriftung. Mit `normalized_mse=0.05726039` lag er oberhalb der
Review-Grenze `0.04594568`.

## Reale Re-Konvertierung

Der Kandidat wurde mit Timeout-Guard und festem Ein-Iterations-Budget aus dem
normalen Eingabeverzeichnis konvertiert:

```bash
timeout 180 env \
  PYTHONPATH=vendor/linux-py310/site-packages:. \
  PYENV_VERSION=3.10.20 \
  ICC_MAX_ITERATIONS=1 \
  python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir artifacts/images_to_convert \
  --output-dir /tmp/ic-ac0835-runoh \
  --start AC0835_L \
  --end AC0835_L \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Ergebnis: Exit `0`, semantischer Badge-Pfad mit `label=VOC`. Die Ausgabe behält
die Quellabmessungen `25x25`, enthält ausschließlich Kreis und horizontalen
`VOC`-Text und übernimmt keinen Connector aus dem fehlerhaften Altartefakt.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `11170.070312` | `7629.902344` |
| `normalized_mse` | `0.05726039` | `0.03911266` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Damit verbessert sich `mean_delta2` um `3540.167969` beziehungsweise rund
`31.69 %`; der Kandidat liegt nach dem Lauf unter der Review-Grenze.

## Perception-Lerneffekt und Rotation

Die PF8-Frage wird als **generalisiert** abgeschlossen: Der dominante Kreis
wurde bereits im Linkage-Report als `circle` erkannt und dem allgemeinen
`CircleBackground`-Seed zugeordnet. Die reale Konvertierung bestätigt, dass
Beschreibung, allgemeine AC08-Kreis-/Textgeometrie und der bildbasierte Fit
ausreichen; es wurde kein Sample-SVG als Vorlage übernommen.

Das verbesserte SVG ersetzt den fehlerhaften committeten Altbestand. Ein
Regressionstest rendert dieses Artefakt erneut und erzwingt die Review-Grenze.
`AC0835_L` wurde aus Triage, PF8-Zielen und Linkage-Report entfernt. Die vier
verbleibenden aktiven Kandidaten sind synchron `AC0922_S`, `AC0414_S`,
`AC0130_M` und `AC0130`; die nächste Rotation beginnt mit `AC0922_S`.

## Abschluss

Run OH ist vollständig abgeschlossen: reale Re-Konvertierung grün,
Kreis-/VOC-Semantik korrekt, messbare Qualitätsverbesserung unter die
Review-Grenze, PF8-Lerneffekt abgeschlossen und Kandidatenrotation aktualisiert.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0835-L-Reallauf, Artefakt-Review, PF8-Linkage und gezielte Regressionstests.
- **Ergebnis:** `mean_delta2` von `11170.070312` auf `7629.902344` gesenkt; `normalized_mse=0.03911266` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; verbleibende Abweichung betrifft Text-Rasterung und Grauwert-Antialiasing.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0922_S.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
