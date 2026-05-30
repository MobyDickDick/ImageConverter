# Perception-First-Aufgaben – von Bildhinweisen zu Geometry-IR (2026-05-30)

## Ziel

Die bisherige Geometry-IR löst eine wichtige konzeptionelle Hürde: bekannte
Beschreibungen können als strukturierte SVG-Primitive gerendert werden, statt im
Non-Composite-Fallback rein generisch angenähert zu werden. Die nächste Hürde ist
nun, dass einfache Bildhinweise und Bildinhalte vor der ersten Iteration erkannt
werden, damit nicht jedes Kandidatenbild manuell in Spezialgeometrie übersetzt
werden muss.

Dieses Backlog leitet daraus konkrete Folgeaufgaben ab. Es soll in den nächsten
Arbeitspaketen parallel zur Plan-B-Rotation abgearbeitet werden: pro Paket genau
ein kleiner Perception-Schritt plus ein eng begrenzter Repro-/Qualitätsnachweis.

## Leitprinzipien

1. **Perception vor Iteration:** Zuerst robuste Kandidaten erkennen, danach erst
   rendern, vergleichen und optimieren.
2. **Beschreibung als Suchhinweis:** Text wie „oben mittig ist ein `-`-Zeichen“
   soll eine Region of Interest und einen erwarteten Primitivtyp ableiten.
3. **Geometry-IR bleibt Zielrepräsentation:** Erkennungsergebnisse werden nicht
   direkt als ad-hoc-SVG geschrieben, sondern als Kandidaten für Geometry-IR-
   Elemente verwendet.
4. **Kleine, messbare Schritte:** Jeder Schritt braucht ein synthetisches Minimal-
   Repro, mindestens einen echten Bildkandidaten und eine Log-/Metrikspur.
5. **Keine neue Handarbeitsfalle:** Neue Regeln sollen auf Familien von Formen
   zielen, nicht nur auf exakt ein Dateinamen-Sonderverhalten.

## Aufgabenpakete

### PF1 – Detection-Contract v1 für erkannte Primitive festlegen

- **Problem:** Aktuelle Erkennungshilfen liefern uneinheitliche Rückgaben; für
  den Hauptpfad braucht es ein stabiles Zwischenformat.
- **Umsetzung:** Ein maschinenlesbares Schema für erkannte Primitive definieren:
  `kind`, `bbox`, `center`, geometrische Parameter, Farbe, `confidence`, `roi`,
  `evidence` und Quelle (`hough`, `contour`, `ocr`, `description_hint`, ...).
- **Akzeptanz:** Mindestens Linien-, Kreis-/Ring- und Rechteckkandidaten können
  in dasselbe Format serialisiert und in einem Report ausgegeben werden.
- **Plan-B-Kopplung:** Falls reale Bilder zu unsicher sind, zuerst mit drei
  synthetischen Szenen (`minus`, `circle`, `rectangle`) arbeiten.

### PF2 – Horizontalstrich-/Minus-Erkennung mit ROI-Hinweis implementieren

- **Problem:** Hinweise wie „oben mittig ist ein `-`-Zeichen“ werden noch nicht
  vor der ersten Iteration als konkreter Kandidat genutzt.
- **Umsetzung:** Eine einfache horizontale Linien-/Minus-Erkennung ergänzen:
  Canny/Hough oder Kontur-Bounding-Box, optional eingeschränkt durch ROI aus der
  Beschreibung (`oben`, `mittig`, `links`, `rechts`).
- **Akzeptanz:** Ein synthetisches `-` oben mittig und mindestens ein echtes Bild
  erzeugen einen `HorizontalRule`- oder `TextGlyph("-")`-Kandidaten mit
  plausibler Position, Länge, Strichstärke und Confidence.
- **Plan-B-Kopplung:** Wenn kein echter Kandidat sicher ist, wird ein
  Plan-B-Syntheseprobe-Bild mit bewusst verrauschtem Minuszeichen erzeugt.

### PF3 – Kreis-/Ring-Erkennung als Geometry-IR-Seed stabilisieren

- **Problem:** Viele erfolgreiche Geometry-IR-Fälle beginnen mit einem Kreis oder
  Ring, aber die Erkennung und die beschreibungsgetriebene CircleBackground-IR
  sind noch nicht konsequent gekoppelt.
- **Umsetzung:** Vorhandene Kreis-/Maskenlogik in einen Perception-Kandidaten
  überführen und als bevorzugten Seed für `CircleBackground` verwenden.
- **Akzeptanz:** Mindestens ein AC02-Kompressor-/Ventilkandidat und ein AC08-
  Kreis-/Connector-Kandidat protokollieren denselben Circle-Kandidaten im
  Perception-Report.
- **Plan-B-Kopplung:** Bei instabiler Realbild-Erkennung zuerst synthetische
  Kreis-/Ring-Szenen mit JPEG-Weichzeichnung prüfen.

### PF4 – Perception-Kandidaten vor dem generischen Non-Composite-Fallback nutzen (erledigt 2026-05-30)

- **Problem:** Selbst wenn Erkennungskandidaten existieren, startet der
  Fallback-Pfad bisher nicht systematisch aus diesen Kandidaten.
- **Umsetzung:** Einen kleinen Hook einführen:
  Beschreibung + Bildanalyse → Perception-Kandidaten → Geometry-IR-Vorschlag →
  Render/Fehlerbewertung → erst danach generischer Element-Fit.
- **Akzeptanz:** Validation-Logs unterscheiden sichtbar zwischen
  `description_geometry_ir`, `perception_seeded_geometry_ir` und generischem
  Fallback.
- **Plan-B-Kopplung:** Zunächst nur für `HorizontalRule`/Minus und
  `CircleBackground` freischalten, damit der Scope klein bleibt.
- **Ergebnis 2026-05-30:** Runtime-Hook `non_composite_perception_seeded_geometry_ir` ergänzt; Seeds für `HorizontalRule`, `CircleBackground` und `RectBorder` werden vor dem generischen Element-Fit gerendert und geloggt. Nachweis: `artifacts/evaluation/perception_seeded_geometry_ir_v1/perception_seeded_geometry_ir_report_v1.json`.

### PF5 – Evaluationsharness für Perception-Seeds aufbauen (erledigt 2026-05-30)

- **Problem:** Ohne Metriken lässt sich nicht unterscheiden, ob Erkennung nur
  Einzelfälle rettet oder echte Automatisierung verbessert.
- **Umsetzung:** Ein kleines Tool oder ein Testmodul ergänzen, das synthetische
  und reale Kandidaten ausführt und Precision/Recall, Confidence-Verteilung,
  Renderfehler vor/nach Seed sowie gewählten Call-Path ausgibt.
- **Akzeptanz:** Ein Report zeigt für mindestens drei Primitive (`minus/line`,
  `circle/ring`, `rectangle`) Trefferquote und Qualitätsänderung gegenüber dem
  bisherigen Startpunkt.
- **Plan-B-Kopplung:** Falls reale Bilddaten fehlen, bleibt der Report mit
  synthetischen Fixtures grün und markiert Realbildfälle als offen.
- **Ergebnis 2026-05-30:** `tools/perception_detection_contract.py --report perception-seed-eval` schreibt einen JSON/CSV-Harness mit Top-Candidate-Precision, Detection-/Seed-Recall, Confidence-Verteilung und Fehlerdelta vor/nach Seed für `minus_line`, `circle_ring` und `rectangle`. Nachweis: `artifacts/evaluation/perception_seed_evaluation_v1/`.

### PF6 – Perception-Telemetrie in bestehende Reports integrieren (erledigt 2026-05-30)

- **Problem:** In Folgearbeiten muss nachvollziehbar sein, ob ein Bild wegen
  Erkennung, Beschreibung oder manuellem Geometry-IR-Sonderfall funktioniert.
- **Umsetzung:** Pro Lauf eine CSV/JSON-Spur schreiben: erkannte Kandidaten,
  abgelehnte Kandidaten, Gründe, gewählter Geometry-IR-Seed, Fehlerwert vor/nach
  Seed.
- **Akzeptanz:** Ein Einzelrun für einen Plan-B-Kandidaten erzeugt einen
  Perception-Report, der im nächsten Arbeitspaket als Entscheidungsgrundlage
  genutzt werden kann.
- **Plan-B-Kopplung:** Wenn der Hauptpfad noch nicht schreibt, zunächst ein
  externes Tool `tools/...` verwenden und später in den Runtime-Pfad ziehen.
- **Ergebnis 2026-05-30:** `tools/perception_detection_contract.py --report perception-telemetry` schreibt `perception_telemetry_report_v1.json` und `perception_telemetry_candidates_v1.csv` mit Kandidatenentscheidungen, gewählten Geometry-IR-Seeds sowie Fehlerwerten vor/nach Seed. Nachweis: `artifacts/evaluation/perception_telemetry_v1/`.

### PF7 – Einfache Text-/Glyph-Erkennung für `M`, `+`, `-` und kurze Labels prüfen

- **Problem:** Mehrere Symbolfamilien enthalten kleine Buchstaben oder Zeichen;
  vollständiges OCR wäre überdimensioniert, aber wenige Glyphen sind wertvoll.
- **Umsetzung:** Eine Minimalstrategie evaluieren: Template-Matching oder OCR nur
  für kleine, bekannte Zeichenklassen (`M`, `+`, `-`, kurze Labels wie `rF`).
- **Akzeptanz:** Für synthetische Glyphen und mindestens einen echten
  Kellen-/Ventilkandidaten wird dokumentiert, ob Template-Matching genügt oder
  ein OCR-Backend nötig ist.
- **Plan-B-Kopplung:** Wenn OCR-Abhängigkeiten den Lauf erschweren, bleibt die
  Aufgabe auf Template-Matching ohne neue Pflichtdependency begrenzt.

### PF8 – Plan-B-Rotation mit Perception-Aufgaben verzahnen

- **Problem:** Die Plan-B-Liste verhindert Stillstand, kann aber in lineares
  Nachzeichnen abrutschen.
- **Umsetzung:** Jedes kommende Plan-B-Arbeitspaket wählt zusätzlich genau eine
  Perception-Frage: Welches Primitive hätte vor der ersten Iteration erkannt
  werden können, und wie wird dieses künftig als Seed dokumentiert?
- **Akzeptanz:** Die nächsten Plan-B-Dokumente enthalten je einen Abschnitt
  „Perception-Lerneffekt“ mit Entscheidung: `generalisiert`, `nur Sonderfall`,
  `noch nicht erkannt`.
- **Plan-B-Kopplung:** Bei `AC0224_S`, `AC0231_S`, `AC0838_M` und `AC0881_M`
  jeweils vorab festhalten, welches einfache Primitive zuerst erkannt werden
  soll.

## Empfohlene Reihenfolge für die nächsten Arbeitspakete

1. **PF1** als Grundlage: gemeinsames Datenformat für erkannte Primitive.
2. **PF2** als kleinstes Nutzerbeispiel: „oben mittig ist ein `-`-Zeichen“.
3. **PF6** früh einziehen, damit die folgenden Schritte nicht wieder unsichtbar
   bleiben. (erledigt 2026-05-30)
4. **PF3/PF4** koppeln, sobald `minus/line` stabil protokolliert wird.
5. **PF5** nach den ersten zwei erkannten Primitiven, damit Fortschritt messbar
   bleibt. (erledigt 2026-05-30)
6. **PF7/PF8** laufend mit der Plan-B-Rotation verbinden.

## Definition of Done für den Perception-First-Track

Der Track gilt nicht schon dann als erledigt, wenn einzelne Bilddateien bessere
SVGs erhalten. Er gilt erst als belastbar, wenn mindestens drei Primitive vor der
ersten Iteration erkannt, als Geometry-IR-Seeds verwendet und in Reports mit
Qualitätsänderung dokumentiert werden.
