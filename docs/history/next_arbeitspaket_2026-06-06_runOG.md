# Nächstes Arbeitspaket – Qualitätsrefresh und Plan-B-Triage Run OG (2026-06-06)

## Ziel

Nach dem Abschluss von `AC0864_S` aktualisiert Run OG die Qualitätsreports und
kuratiert daraus eine neue, noch nicht erledigte Plan-B-/Perception-Rotation.
Der Review soll nicht erneut als einmaliger Inline-Code enden, sondern
reproduzierbar und per Regressionstest abgesichert sein.

## Umsetzung

`tools/review_conversion_quality.py` prüft die bisherige Erfolgsliste und das
vorhandene Diff-Inventar gegen Originalbilder und aktuelle SVG-Artefakte. Das
Tool schreibt je Variante Pfade, Dimensionen, Status, `mean_delta2` und
`normalized_mse` in CSV sowie eine zusammengefasste JSON-Entscheidung.

Die Kandidatenauswahl ist begrenzt und deterministisch:

1. rote oder unvollständige Einträge aus `successed_conversions.txt` zuerst,
2. danach renderbare Diff-Fälle oberhalb der Review-Grenze,
3. höchstens `3200` Pixel Bildfläche, keine `_sia`-Spezialvarianten,
4. insgesamt maximal fünf aktive Kandidaten.

## Qualitätsbefund

- `48/48` Einträge der Erfolgsliste sind renderbar.
- `1/48` liegt oberhalb der Review-Grenze: `AC0835_L` mit `0.05726039`.
- `121/131` Diff-Inventarvarianten besitzen ein renderbares Bild-/SVG-Paar.
- Die neue Rotation lautet `AC0835_L`, `AC0922_S`, `AC0414_S`, `AC0130_M`, `AC0130`.

## PF8-Linkage

Plan-B-Liste, Triage-CSV und PF8-Ziele enthalten dieselben fünf Varianten in
derselben Reihenfolge. Der neu erzeugte Linkage-Report wertet alle fünf Bilder
aus: vier Lerneffekte sind `generalisiert`, `AC0130_M` bleibt wegen des noch
fehlenden allgemeinen Rechteck-Seeds `nur Sonderfall`; kein Kandidat ist
`noch nicht erkannt`.

## Abschluss

Run OG ist vollständig abgeschlossen. Die Qualitätsauswertung ist
reproduzierbar, die aktive Rotation wieder gefüllt und der erste Folgepunkt
fachlich festgelegt.

## 5-Zeilen-Log

- **Getestet:** Review-Tool, Auswahlpolicy, Reportserialisierung und PF8-Linkage-Synchronität.
- **Ergebnis:** 48 Erfolgsvarianten und 131 Diff-Fälle geprüft; fünf aktive Kandidaten kuratiert.
- **Blocker:** Kein Triage-Blocker; `AC0130_M` besitzt noch keinen generalisierten Rechteck-Seed.
- **Nächster Schritt:** `AC0835_L.jpg` real re-konvertieren und Kreis-/VOC-Perception-Lerneffekt abschließen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
