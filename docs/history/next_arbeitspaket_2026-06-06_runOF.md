# Nächstes Arbeitspaket – Plan-B AC0864_S Run OF (2026-06-06)

## Ziel

Run OF arbeitet den letzten aktiven Kandidaten der dokumentierten
Plan-B-/Perception-Rotation ab: `AC0864_S.jpg`. Die Beschreibung definiert das
Symbol als horizontale Spiegelung von `AC0862`: ein rundes `rF`-Badge mit
horizontal bleibendem Text und Connector rechts vom Kreis.

## Implementierung

`AC0864` ist jetzt eine reguläre semantische AC08-Badge-Familie. Die
Familienregeln liefern das `rF`-Label und den rechten horizontalen Connector;
die Parametererzeugung verwendet die allgemeine AC0814-Rechtsarm-Geometrie
mit dem vorhandenen bildbasierten Fitting. Der Small-Variant-Kreisfallback
wurde für die 25x15-Variante freigeschaltet. Es wurden weder ein Sample-SVG
noch bildspezifische Pixelkoordinaten übernommen.

Regressionstests sichern sowohl die Familienbeschreibung als auch die
Geometrie: Der Connector liegt rechts vom Kreismittelpunkt, endet am rechten
Bildrand, bleibt horizontal und wird nicht gleichzeitig als linker Connector
ausgegeben.

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
  --output-dir /tmp/ic-ac0864-run \
  --start AC0864_S \
  --end AC0864_S \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --deterministic-order
```

Ergebnis: Exit `0`, `status=semantic_ok`. Die Ausgabe behält die
Quellabmessungen `25x15` und enthält den Kreis, horizontalen `rF`-Text sowie
den gespiegelten rechten Connector.

| Metrik | Wert |
| --- | ---: |
| `best_iter` | `1` |
| `best_error` | `17.986667` |
| `error_per_pixel` | `0.04796444` |
| `mean_delta2` | `3699.607910` |
| Validierungsstatus | `semantic_ok` |

Die verbleibende Pixelabweichung betrifft vor allem Textdarstellung,
Grauwertabstimmung und Antialiasing; Semantik und Topologie sind korrekt.

## Perception-Lerneffekt und Rotation

Die PF8-Frage ist **generalisiert** abgeschlossen: Der Kandidatenreport vor dem
Lauf erkannte den dominanten Kreis als `CircleBackground` sowie einen
Linienkandidaten für den Connector. Die Konvertierung bestätigt, dass diese
allgemeinen Hinweise zusammen mit Beschreibung und AC08-Familienregeln für die
gespiegelte Ausgabe ausreichen.

`AC0864_S` wurde aus der aktiven maschinenlesbaren Zielliste entfernt. Da damit
alle freigegebenen Kandidaten der dokumentierten Rotation erledigt sind, sind
Plan-B-Liste und Linkage-Report jetzt bewusst leer (`samples=0`,
`evaluated_samples=0`, `all_have_perception_lerneffekt=true`). Ein
Regressionstest hält diesen Zustand synchron. Eine neue Rotation beginnt erst
nach einer aktualisierten Qualitätsauswertung und Kandidatentriage.

## Abschluss

Run OF ist vollständig abgeschlossen: reale Konvertierung grün,
`status=semantic_ok`, korrekte Spiegelgeometrie und Dimensionen, PF8-Entscheid
abgeschlossen und die aktive Rotation sauber geleert.

## 5-Zeilen-Log

- **Getestet:** Isolierter AC0864-S-Reallauf, gezielte Semantik-/Geometrietests, PF8-Linkage-Generierung und Kernsuite.
- **Ergebnis:** AC0864_S erzeugt ein semantisch korrektes 25x15-Badge mit rechtem Connector, Kreis und horizontalem rF-Text; `mean_delta2=3699.607910`.
- **Blocker:** Kein technischer Blocker; Restabweichung betrifft Text-/Antialiasingdetails.
- **Nächster Schritt:** Qualitätsreports aktualisieren und daraus eine neue, noch nicht erledigte Plan-B-Rotation kuratieren.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m pytest -q tests/test_plan_b_perception_linkage.py tests/test_image_composite_converter.py -k 'ac0864 or plan_b_perception'`.
