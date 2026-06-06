# Nächstes Arbeitspaket – Plan-B AC0863_S Run OE (2026-06-06)

## Ziel

Nach dem grünen Abschluss des Finish-Playbooks setzt Run OE die reguläre
Plan-B-/Perception-Rotation mit dem ersten aktiven Kandidaten `AC0863_S.jpg`
fort. Die Familie war bereits allgemein als semantisches AC08-`rF`-Badge mit
oberem vertikalem Connector modelliert; offen waren der reale Kandidatenlauf,
der Qualitätsnachweis und die saubere Rotation der aktiven PF8-Liste.

## Reale Konvertierung

Der Kandidat wurde mit festem Ein-Iterations-Budget und Timeout-Guard aus dem
normalen Eingabeverzeichnis konvertiert:

```bash
timeout 180 env \
  PYTHONPATH=vendor/linux-py310/site-packages:. \
  PYENV_VERSION=3.10.20 \
  ICC_MAX_ITERATIONS=1 \
  python -m src.iCCModules.imageCompositeConverterCli \
  --input-dir artifacts/images_to_convert \
  --output-dir /tmp/ic-ac0863-run \
  --start AC0863_S \
  --end AC0863_S \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Ergebnis: Exit `0`; die Beschreibung wird als
`SEMANTIC: senkrechter Strich oben vom Kreis` plus
`SEMANTIC: Kreis + Buchstabe rF` interpretiert. Das erzeugte SVG hat dieselben
Abmessungen wie die Quelle (`15x25`) und enthält genau den oberen Connector,
den Kreis und horizontalen `rF`-Text.

| Metrik | Wert |
| --- | ---: |
| `best_iter` | `1` |
| `best_error` | `18.522667` |
| `error_per_pixel` | `0.04939378` |
| `mean_delta2` | `4155.215820` |
| Validierungsstatus | `semantic_ok` |

Damit ist der Kandidat nicht mehr `conversion_failed`; der verbleibende
Pixelabstand liegt wie bei den benachbarten kleinen rF-Badges überwiegend im
Text-/Antialiasingbereich und ist kein Semantik- oder Topologiefehler.

## Perception-Lerneffekt und Rotation

Die verpflichtende PF8-Frage für `AC0863_S` wird als **generalisiert**
abgeschlossen: Der dominante Kreis wird als `CircleBackground` erkannt, und
die Erkennung liefert zusätzlich einen Linienkandidaten für den Connector.
Die eigentliche semantische Ausgabe bleibt algorithmisch aus Beschreibung,
Bildsignal und der allgemeinen AC08-Badge-Geometrie erzeugt; es wurde kein
Sample-SVG oder fester Bilddatensatz übernommen.

`AC0863_S` und der bereits erledigte Vorgänger `AC0862_S` wurden aus der
aktiven maschinenlesbaren PF8-Zielliste entfernt. Der neu erzeugte Linkage-
Report enthält nun ausschließlich den nächsten aktiven Kandidaten
`AC0864_S`, mit `samples=1`, `evaluated_samples=1` und
`all_have_perception_lerneffekt=true`. Ein Regressionstest hält die aktive
Zielliste und den Report synchron, damit erledigte Kandidaten künftig nicht
weiter als offen ausgewiesen werden.

## Abschluss

Run OE ist vollständig abgeschlossen: reale Konvertierung grün,
`status=semantic_ok`, korrekte Geometrie und Dimensionen, PF8-Entscheidung
dokumentiert und Kandidatenrotation auf `AC0864_S` nachgeführt.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0863-S-Reallauf, PF8-Linkage-Generierung, gezielte Semantik-/Perception-Tests und Kernsuite.
- **Ergebnis:** AC0863_S erzeugt ein semantisch korrektes 15x25-SVG mit oberem Connector, Kreis und horizontalem rF-Text; `mean_delta2=4155.215820`.
- **Blocker:** Kein technischer Blocker; Restabweichung betrifft Text-/Antialiasingdetails.
- **Nächster Schritt:** Die reguläre Plan-B-Rotation mit `AC0864_S.jpg` fortsetzen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m pytest -q tests/test_plan_b_perception_linkage.py tests/test_image_composite_converter.py -k 'ac0863 or plan_b_perception'`.
