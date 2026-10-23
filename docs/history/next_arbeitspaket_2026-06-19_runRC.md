# Nächstes Arbeitspaket – Conversion-Qualitätsranking und Plan-B-Triage Run RC (2026-06-19)

Run RC arbeitet das nächste praktisch notwendige Plan-B-Arbeitspaket ab: Die
lokal erzeugten Diff-/Review-Artefakte werden ausgewertet, die Qualität der
Konvertierungen wird in eine nachvollziehbare Reihenfolge gebracht und die
Plan-B-Rotation wird wieder mit konkreten Kandidaten befüllt.

## 1) Ziel

Die subjektive Sichtprüfung der Diff-Dateien soll durch eine reproduzierbare
Rangliste ersetzt werden. Gleichzeitig soll die Rotation zukünftig nicht mehr
leer bleiben, wenn die Diff-Inventur messbar schlechte, kompakte Kandidaten
enthält.

## 2) Umsetzung

- `tools/review_conversion_quality.py` wurde erneut ausgeführt und hat die
  Artefakte unter `artifacts/evaluation/conversion_quality_review_v2/`
  aktualisiert.
- `docs/conversion_quality_review_2026-06-19_runRC.md` dokumentiert die
  Reihenfolge der besten und schlechtesten Konvertierungen, die Zählung der
  zufriedenstellenden Fälle und die künftige Nutzungsregel für Plan-B.
- `PLAN_B_KANDIDATEN.md` wurde von der leeren Rotation auf die fünf automatisch
  priorisierten Kandidaten aus `plan_b_candidate_triage_v1.csv` umgestellt.

## 3) Ergebnis der Auswertung

- Nach der aktuellen Review-Grenze `normalized_mse <= 0.045945679012345676`
  liegen alle 48 renderbaren erfolgreichen Konvertierungen unter der groben
  technischen Gate-Grenze; das ist kein menschliches Qualitätsurteil.
- Im Diff-Inventar liegen 551 von 630 renderbaren Paaren unterhalb der Review-
  Grenze; 79 liegen darüber.
- Nach der historischen harten Pixelmetrik `mean_delta2 <= 18.000` ist nur 1 von
  678 renderbaren Review-Paaren pixelnah. Das bestätigt den Eindruck, dass die
  Diff-Dateien optisch fast durchgehend problematisch wirken, wenn man nahezu
  pixelgenaue Rasterähnlichkeit erwartet.
- Die Diskrepanz ist erklärbar: `mean_delta2 <= 18` erlaubt nur rund 2.45
  mittlere RGB-Stufen Fehler pro Farbkanal, während die aktuelle Review-Grenze
  ungefähr 55 RGB-Stufen pro Farbkanal zulässt. Die bisherige Bezeichnung
  „zufriedenstellend“ für die lockere Grenze war daher irreführend.
- Die neue Plan-B-Reihenfolge lautet: `GE9002_7S`, `GE9002_5S`, `GE9002_3S`,
  `GE9002_4M`, `GE9002_1S`.

## 4) Nachweis

- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/review_conversion_quality.py`
  → Exit `0`; `successful_renderable_pairs=48`, `diff_renderable_pairs=630`,
  `selected_candidates=5`.

## 5) Nächster Schritt

Die reguläre Plan-B-Rotation mit `GE9002_7S` fortsetzen und dabei den
Perception-Lerneffekt für die GE9002-Familie dokumentieren.
