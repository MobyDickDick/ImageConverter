# Nächstes Arbeitspaket – Plan-B AC0531_1_S Run OQ (2026-06-08)

## Ziel

Run OQ arbeitet den nächsten in Run OP dokumentierten Kandidaten vollständig
ab: `AC0531_1_S.jpg`. Das bisherige SVG enthielt zwei Diagonalen und ein
Pluszeichen, obwohl die XML-Beschreibung genau eine Diagonale von unten links
nach oben rechts sowie einen dunkelgrauen Mittelpunkt fordert. Mit
`normalized_mse=0.15610678` lag der Kandidat deutlich über der Review-Grenze
`0.04594568`.

## Reale Re-Konvertierung

```bash
timeout 240 env \
  PYTHONPATH=vendor/linux-py310/site-packages:. \
  PYENV_VERSION=3.10.20 \
  ICC_MAX_ITERATIONS=1 \
  python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir artifacts/images_to_convert \
  --output-dir /tmp/ic-ac0531-run6 \
  --start AC0531_1_S \
  --end AC0531_1_S \
  --descriptions-path artifacts/descriptions/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Ergebnis: Exit `0`, dimensionstreues `20x40`-SVG und Auswahl des allgemeinen
`non_composite_elementwise_symbol_fit`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `30452.529297` | `4837.790039` |
| `normalized_mse` | `0.15610678` | `0.02479964` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung beträgt `25614.739258` beziehungsweise rund `84.11 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Der allgemeine Element-Fit unterscheidet nun anhand der Beschreibung zwischen
einzelner und doppelter Diagonale, Plus-/Minus-Glyphen und einem mittigen
Punkt. Nicht deklarierte Glyphen werden nicht mehr durch opportunistische
Pixeloptimierung erfunden. Robuste Spaltenmediane schätzen den horizontalen
Farbverlauf, während ein ausgedehntes Helligkeitsresiduum Farbe und gekürzte
Ausdehnung der Diagonale bestimmt. OpenCV-BGR-Farben werden dabei korrekt in
SVG-RGB übertragen. Es wurden weder ein Kandidaten-SVG noch feste
AC0531-Koordinaten in den Algorithmus aufgenommen.

Die PF8-Frage ist **generalisiert**: Rechteck, Linie und Kreis-/Ringkandidaten
waren bereits allgemein erkennbar; der Runtime-Fit nutzt nun zusätzlich die
Beschreibung, um genau die geforderte Diagonal-/Mittelpunkt-Topologie zu
rendern. Regressionstests sichern Primitive, Farberhalt und Qualitätsgrenze.

## Rotation

`AC0531_1_S` wurde aus Triage und PF8-Zielen entfernt. Der reproduzierbare
Review füllt mit `AC0253_1` auf. Die aktiven Kandidaten sind nun
`AC0502_1_M`, `AC0551_1_M`, `AC0403_1_M`, `AC0150_2` und `AC0253_1`.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0531-1-S-Reallauf, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `84.11 %` auf `4837.790039` gesenkt; `normalized_mse=0.02479964` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; verbleibende Abweichung betrifft hauptsächlich JPEG-Antialiasing und Randfarben.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0502_1_M.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_non_composite_runtime_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
