# Conversion-Qualitätsauswertung – Run RC (2026-06-19)

Diese Auswertung ist die neue Reihenfolge für künftige Plan-B-Pakete. Sie basiert auf `tools/review_conversion_quality.py` und den erzeugten Artefakten unter `artifacts/evaluation/conversion_quality_review_v2/`.

## Zählung

- Review-Grenze: `normalized_mse <= 0.045945679012345676` beziehungsweise ungefähr `mean_delta2 <= 8963`.
- Renderbare erfolgreiche Konvertierungen: **48 / 48 unter dieser Review-Grenze**. Das ist nur eine grobe technische Gate-Grenze, kein menschliches Qualitätsurteil.
- Renderbare Diff-Inventar-Paare: **551 / 630 unter der Review-Grenze**, **79** oberhalb der Grenze.
- Gesamte renderbare Review-Menge: **599 / 678 unter der Review-Grenze**.
- Historische harte Altmetrik `mean_delta2 <= 18.000`: **1 / 678**. Damit bestätigt die lokale Auswertung Dein Bauchgefühl für die Diff-Dateien: nach der alten Pixelmetrik liegt die nahezu pixelgenaue Trefferquote bei nur **0.15 %**.

## Warum fallen 98,85 % durch die harte Altmetrik?

`mean_delta2` ist die mittlere Summe der quadrierten RGB-Abstände pro Pixel. Eine Grenze von `18.000` entspricht nur ungefähr `sqrt(18 / 3) = 2.45` Helligkeitsstufen mittlerem Fehler pro Farbkanal. Das ist nahezu ein Pixel-Identitätskriterium. Schon kleine Verschiebungen, andere Antialiasing-Kanten, abweichende Strichstärken, Text-Rendering oder eine semantisch richtige, aber geometrisch leicht anders platzierte SVG-Primitive überschreiten diese Grenze sofort.

Die aktuelle Review-Grenze ist dagegen extrem viel lockerer: `normalized_mse <= 0.045945679012345676` entspricht etwa `mean_delta2 <= 8963` beziehungsweise rund `55` mittleren RGB-Stufen pro Farbkanal. Deshalb können gleichzeitig **88,35 %** der renderbaren Paare unter der groben Review-Grenze liegen, während nur **0,15 %** pixelgenau genug für die harte Altmetrik sind.

Das heißt nicht automatisch, dass das komplette Design falsch ist. Es zeigt aber zwei echte Probleme:

1. **Die bisherige Review-Grenze ist als „zufriedenstellend“ zu weich benannt.** Sie taugt als grober Regression-/Triage-Filter, aber nicht als Abnahmekriterium für sichtbare Qualität.
2. **Die aktuelle Konvertierung optimiert noch zu oft auf eine grobe semantische oder primitive SVG-Rekonstruktion statt auf visuell enges Pixel-Fitting.** Für Diff-Dateien wirken deshalb auch viele technisch „unter Grenze“ liegende Ergebnisse unbefriedigend.

Für Plan B verwende ich deshalb ab jetzt nicht mehr die Formulierung „zufriedenstellend“ für die lockere Review-Grenze, sondern trenne:

- **pixelnah:** `mean_delta2 <= 18`, praktisch exakte Rasterähnlichkeit,
- **technisch unter Review-Grenze:** `normalized_mse <= 0.045945679012345676`, grober Triage-Erfolg,
- **Plan-B-kritisch:** oberhalb der Review-Grenze oder sichtbar stark abweichend trotz niedrigerem Wert.

## Beste Konvertierungen nach `normalized_mse`

| Rang | Variante | Quelle | normalized_mse | mean_delta2 | Status |
|---:|---|---|---:|---:|---|
| 1 | `DLG0040` | `diff_inventory` | 0.00000000 | 0.000 | `ok` |
| 2 | `GE1300_S` | `diff_inventory` | 0.00019103 | 37.265 | `ok` |
| 3 | `GE9006_4S` | `diff_inventory` | 0.00026656 | 52.000 | `ok` |
| 4 | `AC0800_M` | `successful_conversion` | 0.00027636 | 53.910 | `ok` |
| 5 | `GE9001_4S` | `diff_inventory` | 0.00034038 | 66.400 | `ok` |
| 6 | `GE1312_M` | `diff_inventory` | 0.00040379 | 78.770 | `ok` |
| 7 | `GE9901_S` | `diff_inventory` | 0.00097920 | 191.017 | `ok` |
| 8 | `AC0224_S` | `diff_inventory` | 0.00114221 | 222.817 | `ok` |
| 9 | `AC0222_S` | `diff_inventory` | 0.00114236 | 222.847 | `ok` |
| 10 | `GE9006_4M` | `diff_inventory` | 0.00125131 | 244.100 | `ok` |
| 11 | `AC0224_M` | `diff_inventory` | 0.00125914 | 245.626 | `ok` |
| 12 | `SH_Objekt2` | `diff_inventory` | 0.00126656 | 247.073 | `ok` |
| 13 | `GE0010` | `diff_inventory` | 0.00142305 | 277.601 | `ok` |
| 14 | `AC0130_M` | `diff_inventory` | 0.00153867 | 300.156 | `ok` |
| 15 | `GE9902_W` | `diff_inventory` | 0.00170646 | 332.888 | `ok` |
| 16 | `GE9902_S` | `diff_inventory` | 0.00182766 | 356.531 | `ok` |
| 17 | `AC0703_1_L` | `diff_inventory` | 0.00192707 | 375.924 | `ok` |
| 18 | `bg_deco_norm` | `diff_inventory` | 0.00196063 | 382.470 | `ok` |
| 19 | `GE0011` | `diff_inventory` | 0.00203447 | 396.874 | `ok` |
| 20 | `AC0701_1_S` | `diff_inventory` | 0.00218365 | 425.976 | `ok` |

## Schlechteste Konvertierungen nach `normalized_mse`

| Rang | Variante | Quelle | normalized_mse | mean_delta2 | Status |
|---:|---|---|---:|---:|---|
| 1 | `GE1312_S` | `diff_inventory` | 0.96003116 | 187278.078 | `ok` |
| 2 | `GE9002_7S` | `diff_inventory` | 0.42523953 | 82953.602 | `ok` |
| 3 | `GE9002_5S` | `diff_inventory` | 0.36928157 | 72037.602 | `ok` |
| 4 | `GE9002_3S` | `diff_inventory` | 0.34951533 | 68181.703 | `ok` |
| 5 | `GE9002_4M` | `diff_inventory` | 0.34297169 | 66905.203 | `ok` |
| 6 | `GE9002_1S` | `diff_inventory` | 0.32676407 | 63743.500 | `ok` |
| 7 | `GE9002_3M` | `diff_inventory` | 0.31557065 | 61559.945 | `ok` |
| 8 | `GE9002_2S` | `diff_inventory` | 0.30556657 | 59608.398 | `ok` |
| 9 | `GE9002_2M` | `diff_inventory` | 0.28281867 | 55170.852 | `ok` |
| 10 | `GE9002_6S` | `diff_inventory` | 0.24947686 | 48666.699 | `ok` |
| 11 | `AC0302_1L_sia` | `diff_inventory` | 0.18763468 | 36602.836 | `ok` |
| 12 | `AC5041_M` | `diff_inventory` | 0.14297610 | 27891.062 | `ok` |
| 13 | `AC0403_1L_sia` | `diff_inventory` | 0.12435253 | 24258.070 | `ok` |
| 14 | `AC0304_2_M` | `diff_inventory` | 0.11500499 | 22434.598 | `ok` |
| 15 | `GE0016` | `diff_inventory` | 0.11236529 | 21919.658 | `ok` |
| 16 | `AC0304_1L_sia` | `diff_inventory` | 0.10288458 | 20070.209 | `ok` |
| 17 | `DLG0051` | `diff_inventory` | 0.09805104 | 19127.307 | `ok` |
| 18 | `L60x` | `diff_inventory` | 0.09769215 | 19057.297 | `ok` |
| 19 | `GE0302` | `diff_inventory` | 0.08963236 | 17485.033 | `ok` |
| 20 | `GE9014_1S` | `diff_inventory` | 0.08101132 | 15803.283 | `ok` |

## Plan-B-Reihenfolge aus dieser Auswertung

Diese fünf Fälle sind die aktuelle, automatisch reproduzierbare Triage für die nächsten Plan-B-Arbeitspakete.

| Rang | Variante | Quelle | normalized_mse | mean_delta2 | Status |
|---:|---|---|---:|---:|---|
| 1 | `GE9002_7S` | `diff_inventory` | 0.42523953 | 82953.602 | `ok` |
| 2 | `GE9002_5S` | `diff_inventory` | 0.36928157 | 72037.602 | `ok` |
| 3 | `GE9002_3S` | `diff_inventory` | 0.34951533 | 68181.703 | `ok` |
| 4 | `GE9002_4M` | `diff_inventory` | 0.34297169 | 66905.203 | `ok` |
| 5 | `GE9002_1S` | `diff_inventory` | 0.32676407 | 63743.500 | `ok` |

## Nutzungsregel ab jetzt

1. Nach jedem Arbeitspaket `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/review_conversion_quality.py` ausführen.
2. Die Plan-B-Rotation zuerst aus `artifacts/evaluation/conversion_quality_review_v2/plan_b_candidate_triage_v1.csv` auffüllen.
3. Nur Kandidaten überspringen, wenn sie offensichtlich nicht renderbar, hoffnungslos komplex oder gerade bereits bearbeitet wurden; die Begründung dann im nächsten `docs/next_arbeitspaket_*.md` dokumentieren.
4. Die harte Altmetrik `mean_delta2 <= 18.000` bleibt als Pixelnähe-Alarm erhalten. Die lockere Review-Grenze darf nicht mehr als menschlich „zufriedenstellend“ bezeichnet werden.
5. Für Plan-B-Priorisierung zählen künftig zuerst sichtbare Diff-Abweichung und hohe `normalized_mse`-/`mean_delta2`-Werte; semantisch richtige, aber pixelweit entfernte SVGs bleiben Qualitätsfolgepunkte.

## AC0022 als konkretes Beispiel

`AC0022` war ein guter Gegenbeleg gegen die bisherige Logik: Das Bild besitzt
zwei farbige vertikale Pfeile, aber der alte Dual-Arrow-Detektor hat die
Farbmasken implizit als „blau ist links“ und „rot ist rechts“ behandelt, ohne
sie nach ihrer tatsächlichen x-Position im Bild zu sortieren. Dadurch konnte ein
sichtbar falsches Ergebnis trotzdem mit `status=dual_arrow_badge_ok` im
Validierungslog landen.

Die korrigierte Logik sortiert die erkannten roten/blauen Pfeile nach ihrer
physikalischen x-Position und schreibt die jeweilige Farbe an die sortierte
linke/rechte Geometrie. Zusätzlich markiert der Dual-Arrow-Lauf Ergebnisse mit
zu hohem `normalized_mse` jetzt als `status=dual_arrow_badge_quality_failed`,
statt sie pauschal als ok zu protokollieren.

Der erste AC0022-Nachlauf verbesserte `mean_delta2` von `12307.544922` auf
`9926.272461`, lag mit `normalized_mse=0.05088439` aber weiterhin oberhalb der
Review-Grenze. Der zweite Nachlauf ergänzt deshalb eine maskenbasierte
Vektor-Refinement-Stufe für diesen Dual-Arrow-Fall: farbige Vordergrundläufe
werden als SVG-`rect`-Runs ausgegeben, sobald die geometrische Pfeilabstraktion
oberhalb der Review-Grenze bleibt. Damit sinkt AC0022 auf
`mean_delta2=6032.573242` und `normalized_mse=0.03092438`; der Fall gilt nach
der groben Review-Grenze wieder als ausreichend, bleibt aber kein pixelnaher
`mean_delta2 <= 18`-Treffer.
