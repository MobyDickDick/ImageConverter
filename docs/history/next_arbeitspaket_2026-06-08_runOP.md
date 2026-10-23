# Nächstes Arbeitspaket – Plan-B AC0820_L Run OP (2026-06-08)

## Ziel

Run OP arbeitet den ersten Kandidaten der in Run OM kuratierten
Plan-B-/Perception-Rotation vollständig ab: `AC0820_L.jpg`. Der committete
Altbestand enthielt nur einen kleinen Kreis mit rechtem Connector und keine
CO₂-Beschriftung. Mit `normalized_mse=0.05117826` war er der einzige der 48
Erfolgsvarianten oberhalb der Review-Grenze `0.04594568`.

## Reale Re-Konvertierung

Der Kandidat wurde mit Timeout-Guard aus dem normalen Eingabeverzeichnis und
der XML-Bildbeschreibung konvertiert:

```bash
timeout 240 env \
  PYTHONPATH=vendor/linux-py310/site-packages:. \
  PYENV_VERSION=3.10.20 \
  ICC_MAX_ITERATIONS=1 \
  python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir artifacts/images_to_convert \
  --output-dir /tmp/ic-ac0820-runop \
  --start AC0820_L \
  --end AC0820_L \
  --descriptions-path artifacts/descriptions/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Ergebnis: Exit `0`, semantischer Badge-Pfad mit `label=CO_2`. Die Ausgabe
behält die Quellabmessungen `30x30`, enthält einen Kreis sowie getrennten
`CO`- und tiefgestellten `2`-Text und übernimmt keinen Connector aus dem
fehlerhaften Altartefakt.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `9983.599609` | `7458.403320` |
| `normalized_mse` | `0.05117826` | `0.03823352` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Damit verbessert sich `mean_delta2` um `2525.196289` beziehungsweise rund
`25.29 %`; der Kandidat liegt nach dem Lauf unter der Review-Grenze.

## Algorithmische Umsetzung und Perception-Lerneffekt

Die Ausgabe stammt aus dem bestehenden beschreibungsgetriebenen AC08-Pfad:
Die XML-Beschreibung wählt CO₂-Semantik, der allgemeine Badge-Fit bestimmt die
Kreisgeometrie aus dem Bild und die gemeinsame CO₂-Layoutlogik rendert Basis-
und Indextext. Es wurde kein Kandidaten-SVG als Eingabe oder feste Vorlage in
den Algorithmus aufgenommen.

Die PF8-Frage wird als **generalisiert** abgeschlossen: Der dominante Kreis
wurde im Linkage-Report als `circle`/`ring` erkannt und dem allgemeinen
`CircleBackground`-Seed zugeordnet. Ein Regressionstest rendert das committete
SVG erneut, erzwingt die Review-Grenze und prüft zusätzlich Kreis, CO₂-Texte
und Connector-Freiheit.

## Rotation

Der reproduzierbare Review meldet jetzt `0/48` erfolgreiche Varianten oberhalb
der Grenze. `AC0820_L` wurde aus Triage, PF8-Zielen und Linkage-Report entfernt;
aufgefüllt wurde mit `AC0150_2`. Die fünf synchronen Kandidaten sind nun
`AC0531_1_S`, `AC0502_1_M`, `AC0551_1_M`, `AC0403_1_M` und `AC0150_2`.

## Abschluss

Run OP ist vollständig abgeschlossen: reale Re-Konvertierung grün,
Kreis-/CO₂-Semantik korrekt, messbare Qualitätsverbesserung unter die Grenze,
PF8-Lerneffekt abgeschlossen und Kandidatenrotation aktualisiert.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0820-L-Reallauf, Artefakt-Review, PF8-Linkage und gezielte Regressionstests.
- **Ergebnis:** `mean_delta2` von `9983.599609` auf `7458.403320` gesenkt; `normalized_mse=0.03823352` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; verbleibende Abweichung betrifft hauptsächlich Text-Rasterung und Antialiasing.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0531_1_S.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
