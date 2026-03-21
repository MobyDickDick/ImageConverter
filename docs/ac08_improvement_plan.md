# AC08 Verbesserungsplan für den Bildkonverter

## Ziel

Dieser Plan zerlegt die aktuell sichtbaren AC08-Probleme des Bildkonverters in einzeln abarbeitbare Aufgaben.
Die Reihenfolge ist so gewählt, dass zuerst die Auswertbarkeit und Stabilität verbessert werden,
danach die Optimierungslogik, und erst dann familiespezifisches Fine-Tuning erfolgt.

Der Plan basiert auf den aktuellen Reports unter `artifacts/converted_images/reports/` sowie auf der AC08-
Speziallogik in `src/image_composite_converter.py`.

---

## Leitprinzipien

1. **Keine Verschlechterung akzeptieren.**
   Optimierungsschritte dürfen nur übernommen werden, wenn sich der Gesamtfehler nachweislich verbessert.
2. **Stagnation früh erkennen.**
   Wiederholt identische Runden sollen nicht weiter Rechenzeit verbrauchen.
3. **AC08 nur gezielt lockern.**
   Die bestehenden Guards bleiben grundsätzlich erhalten; Lockerungen sollen nur problemorientiert und begrenzt erfolgen.
4. **Familienweise statt einzelfallweise arbeiten.**
   Änderungen werden pro Badge-Familie geplant und validiert, damit keine neuen Inkonsistenzen entstehen.
5. **Messbarkeit vor Feintuning.**
   Erst wenn Logs, Abbruchgründe und Qualitätsmetriken zuverlässig sind, lohnt sich tieferes Geometrie-Tuning.

---

## Arbeitsphasen

## Phase 1 – Auswertung und Guardrails stabilisieren

### Aufgabe 1.1 – Qualitäts-Pass nur bei echter Verbesserung übernehmen ✅ erledigt
**Ziel:** Nachgelagerte Qualitäts-/Tercile-Pässe sollen keine Verschlechterungen mehr einführen.

**Umsetzung:**
- Nach jedem Qualitäts-Pass den Gesamtfehler erneut berechnen.
- Parameteränderungen nur übernehmen, wenn mindestens eine Kernmetrik besser wird:
  - `error_per_pixel` sinkt, und/oder
  - `mean_delta2` sinkt.
- Falls nicht verbessert: Rollback auf den vorherigen Parametersatz.
- Im Log explizit markieren:
  - `accepted_improvement`
  - `rejected_regression`

**Akzeptanzkriterien:**
- In `quality_tercile_passes.csv` gibt es keine angenommenen Verschlechterungen mehr.
- Die Zahl der Fälle mit `improved=1` ist aussagekräftig; Fälle mit Regression werden sauber verworfen.

**Empfohlene Tests:**
- Re-Run für `AC0820..AC0839`
- Vergleich alter/neuer `quality_tercile_passes.csv`

---

### Aufgabe 1.2 – Stagnation der Validierungsrunden früher erkennen ✅ erledigt
**Ziel:** Leere oder redundante Runden sollen nicht mehr mehrfach wiederholt werden.

**Umsetzung:**
- Pro Runde Fingerprint der relevanten Parameter bilden, z. B.:
  - `cx`, `cy`, `r`
  - `arm_len`, `stem_width`, `arm_stroke`
  - `text_scale`, `co2_font_scale`, `voc_scale`
- Wenn zwei Runden hintereinander:
  - den gleichen Parameter-Fingerprint und
  - denselben bzw. praktisch identischen Gesamtfehler haben,
  dann vorzeitig abbrechen oder in einen alternativen Suchmodus wechseln.
- Im Log zusätzliche Marker schreiben:
  - `stagnation_detected`
  - `switch_to_fallback_search`
  - `stopped_due_to_stagnation`

**Akzeptanzkriterien:**
- Problemfälle wie `AC0882_S` laufen nicht mehr über viele identische Runden.
- Die Zahl der Runden sinkt bei stagnierenden Fällen messbar.

**Empfohlene Tests:**
- Einzeltests für `AC0882_S`, `AC0837_M`, `AC0839_S`
- Vergleich der Element-Validation-Logs vor/nach der Änderung

---

### Aufgabe 1.3 – Render-/Batch-Fehler robuster behandeln ✅ erledigt
**Ziel:** Einzelne Renderprobleme dürfen den Batchlauf nicht abbrechen.

**Umsetzung:**
- Render-Schritte mit Fehlerbehandlung versehen.
- Bei Renderfehlern:
  - betroffenen Dateinamen loggen,
  - Zwischenparameter sichern,
  - Batchlauf mit der nächsten Datei fortsetzen.
- Falls möglich: einfachen Retry mit reduziertem Renderpfad oder Fallback aktivieren.
- Eine Fehlerzusammenfassung pro Batch erzeugen.

**Akzeptanzkriterien:**
- Ein einzelner MuPDF-/SVG-Renderfehler stoppt den AC08-Batch nicht mehr vollständig.
- Fehlgeschlagene Dateien werden reproduzierbar geloggt.

**Umgesetzt in Code/Workflow:**
- `Action.render_svg_to_numpy` kapselt Renderer-Ausnahmen und versucht zusätzlich einen normalisierten Retry-Pfad, bevor ein Renderfehler gemeldet wird.
- `run_iteration_pipeline` schreibt bei Renderabbrüchen pro Datei einen `render_failure`-Status inklusive Dateiname, Ursache, Parametersnapshot und bestmöglichem Fehlversuchs-SVG.
- `convert_range` fängt Datei-fehler robust ab, arbeitet den restlichen Batch weiter ab und erzeugt im Report-Ordner eine zentrale `batch_failure_summary.csv`.

**Empfohlene Tests:**
- Batch `AC0800..AC0899`
- Prüfen, ob der Lauf vollständig endet und Fehlerfälle separat ausweist

---

## Phase 2 – Semantik und Initialisierung bereinigen

### Aufgabe 2.1 – AC0811–AC0814 Semantik-Audit einführen ✅ erledigt
**Ziel:** Inkonsistenzen zwischen Beschreibung, Badge-Familie und Text-Erwartung sichtbar machen.

**Umsetzung:**
- Für `AC0811`, `AC0812`, `AC0813`, `AC0814` einen Audit-Output erzeugen mit:
  - Quelldatei
  - Basisname
  - erkannte Beschreibungselemente
  - abgeleitete `params["elements"]`
  - finaler Status (`semantic_ok`, `semantic_mismatch`)
  - Mismatch-Grund
- Audit zuerst als Log/CSV/JSON ausgeben; erst danach Logik anpassen.

**Akzeptanzkriterien:**
- Für jede betroffene Datei ist nachvollziehbar, warum Text erwartet oder nicht erwartet wurde.
- Inkonsistenzen sind nicht mehr nur implizit in den Fehlerlogs verborgen.

**Umgesetzt in Code/Workflow:**
- `Reflection.parse_description` protokolliert jetzt die tatsächlich verwendeten Beschreibungsfragmente samt Lookup-Reihenfolge für Varianten und Basissymbole.
- `run_iteration_pipeline` schreibt für `AC0811..AC0814` strukturierte Audit-Metadaten direkt in die per-Datei-Logs (`semantic_audit_*`), inklusive abgeleiteter `params["elements"]`, Status und Mismatch-Gründen.
- `convert_range` erzeugt zusätzlich die zusammengefassten Reports `semantic_audit_ac0811_ac0814.csv` und `semantic_audit_ac0811_ac0814.json`, damit die betroffenen Familien gesammelt geprüft werden können.

**Empfohlene Tests:**
- Batch `AC0811..AC0814`
- Stichprobe über `_L`, `_M`, `_S`

---

### Aufgabe 2.2 – Prioritätsregeln für Family-Semantik festziehen
**Ziel:** Eindeutige Familienregeln sollen beschreibungsbedingte Fehlinterpretationen übersteuern.

**Umsetzung:**
- Definieren und dokumentieren, welche Quelle Priorität hat:
  1. explizite Family-Regel,
  2. strukturierte Layout-/Badge-Overrides,
  3. heuristische Beschreibungsauswertung.
- Für `AC0811..AC0814` sicherstellen, dass `Kreis ohne Buchstabe` nicht durch weiche Text-Heuristiken überschrieben wird.
- Konflikte explizit loggen statt stillschweigend zu übernehmen.

**Akzeptanzkriterien:**
- Re-Runs für `AC0811..AC0814` erzeugen keine falschen Text-Erwartungen mehr.
- Konfliktfälle sind im Log eindeutig gekennzeichnet.

**Empfohlene Tests:**
- Direkter Vorher/Nachher-Vergleich der betroffenen Semantik-Fehler

---

## Phase 3 – Suchraum für Problemfamilien gezielt öffnen

### Aufgabe 3.1 – Adaptive Locks für AC08-Problemfälle
**Ziel:** Bei klarer Stagnation dürfen ausgewählte Parameter begrenzt freigegeben werden.

**Umsetzung:**
- Für bekannte Problemfamilien adaptive Freigabe einführen, z. B. für:
  - `AC0882`
  - `AC0837`
  - `AC0839`
  - `AC0820`
  - `AC0831`
- Mögliche Freigaben:
  - Farbabweichung in engem Korridor um die kanonische AC08-Palette
  - leicht erweiterte Radius-Brackets
  - größere Freiheit bei Connector-Längen
  - bounded Text-Scaling bei kleinen Varianten
- Freigabe nur dann aktivieren, wenn:
  - Validierung stagniert, oder
  - Elementfehler deutlich oberhalb einer Schwelle bleibt.

**Akzeptanzkriterien:**
- Problemfälle zeigen nach Freigabe messbare neue Kandidatenbewegung.
- Verbesserungen passieren ohne generelle Regression in den stabilen Familien.

**Empfohlene Tests:**
- Fokus-Batch auf die Top-Ausreißer aus `pixel_delta2_ranking.csv`

---

### Aufgabe 3.2 – Separate Regeln für kleine Varianten (`_S`)
**Ziel:** Sehr kleine Varianten sollen nicht mit denselben Annahmen wie `_L`/`_M` behandelt werden.

**Umsetzung:**
- Kleinstvarianten über `min(width, height)` oder Family-Size-Klasse identifizieren.
- Für `_S`-Varianten gesondert tunen:
  - Text-Scale-Fenster
  - Subscript-Offset
  - Mindest-Connector-Länge
  - robustere Masken-/AA-Auswertung
- Loggen, wann der Small-Variant-Modus aktiv war.

**Akzeptanzkriterien:**
- `_S`-Varianten verlieren gegenüber `_L`/`_M` nicht mehr überproportional stark.
- Kritische Fälle wie `AC0882_S`, `AC0834_S`, `AC0839_S` verbessern sich messbar.

**Empfohlene Tests:**
- Nur `_S`-Varianten aller AC08-Familien in einem Sammelbatch

---

## Phase 4 – Familienweise Feinarbeit

### Aufgabe 4.1 – Linke Connector-Familien gemeinsam tunen
**Familien:** `AC0812`, `AC0832`, `AC0837`, `AC0882`

**Ziel:** Linksausrichtung, Arm-Länge und Kreisverankerung gemeinsam stabilisieren.

**Prüfpunkte:**
- Arm bleibt sichtbar und ausreichend lang.
- Kreis kollabiert nicht in Richtung Connector.
- Text bleibt lesbar und zentriert.

---

### Aufgabe 4.2 – Rechte Connector-Familien gemeinsam tunen
**Familien:** `AC0810`, `AC0814`, `AC0833`, `AC0834`, `AC0838`, `AC0839`

**Ziel:** Spiegelbildliche Fälle konsistent behandeln.

**Prüfpunkte:**
- rechter Arm bleibt erhalten,
- Kreis bleibt optisch ausgewogen,
- kleine Varianten driften nicht nach unten/rechts.

---

### Aufgabe 4.3 – Vertikale Connector-Familien gemeinsam tunen
**Familien:** `AC0811`, `AC0813`, `AC0831`, `AC0836`, `AC0881`

**Ziel:** Vertikale Stämme/Arme und Textlage robust auflösen.

**Prüfpunkte:**
- Stem bleibt mittig zum Kreis,
- vertikale Ausdehnung kollabiert nicht,
- CO₂-Text wirkt nicht top-heavy.

---

### Aufgabe 4.4 – Kreis-/Text-Badges separat tunen
**Familien:** `AC0820`, `AC0835`, `AC0870`

**Ziel:** Reine Kreis- und Kreis+Text-Symbole unabhängig von Connector-Heuristiken verbessern.

**Prüfpunkte:**
- Text-Cluster sauber zentriert,
- Ringgröße bleibt plausibel,
- VOC/CO₂-Skalierung ist family-spezifisch stabil.

---

## Phase 5 – Regression und Abschluss

### Aufgabe 5.1 – Kleines AC08-Regression-Set definieren ✅ erledigt
**Ziel:** Künftige Änderungen schnell und reproduzierbar bewerten.

**Vorschlag für das erste feste Set:**
- `AC0882_S`
- `AC0837_L`
- `AC0839_S`
- `AC0820_L`
- `AC0831_L`
- `AC0834_S`
- `AC0835_S`
- `AC0811_L`
- `AC0812_M`

**Akzeptanzkriterien:**
- Das Set deckt Semantikfehler, Stagnation und kleine Varianten ab.
- Jeder Lauf produziert vergleichbare Reports und Logs.

**Umgesetzt in Code/Workflow:**
- Festes Set `ac08_core_9` als kanonische Regression-Teilmenge im Konverter hinterlegt.
- CLI-Schalter `--ac08-regression-set` verarbeitet genau diese neun Varianten statt eines bloßen Bereichsfilters.
- Jeder Lauf schreibt zusätzlich:
  - `ac08_regression_set.csv` mit Fokus/Begründung je Variante,
  - `ac08_regression_summary.txt` mit reproduzierbarem Kommando und erwarteten Reports.

**Reproduzierbarer Aufruf:**
```bash
python -m src.image_composite_converter \
  artifacts/images_to_convert \
  --csv-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --ac08-regression-set \
  128
```

---

### Aufgabe 5.2 – Erfolgskriterien schriftlich festhalten ✅ erledigt
**Ziel:** Abschluss einer Maßnahme objektiv bewerten können.

**Metriken:**
- Anteil der Fälle mit verbessertem `error_per_pixel`
- Anteil der Fälle mit gesunkenem `mean_delta2`
- Anzahl `semantic_mismatch`
- Anzahl Batch-Abbrüche/Renderfehler
- mittlere Zahl der Validierungsrunden pro Datei

**Definition „Maßnahme erfolgreich“:**
- keine neuen Batch-Abbrüche,
- keine angenommenen Regressionen,
- messbare Verbesserung im Regression-Set,
- keine Verschlechterung in stabilen Familien.

**Umgesetzt in Code/Workflow:**
- Läufe mit dem festen Regression-Set `ac08_core_9` schreiben zusätzlich:
  - `ac08_success_metrics.csv` mit den schriftlich festgelegten Abschlussmetriken,
  - `ac08_success_criteria.txt` mit der konkreten Erfolgsdefinition und dem gemessenen Status des aktuellen Laufs.
- Erfasst werden dabei die in dieser Aufgabe geforderten Kennzahlen:
  - `improved_error_per_pixel_count`,
  - `improved_mean_delta2_count`,
  - `semantic_mismatch_count`,
  - `batch_abort_or_render_failure_count`,
  - `mean_validation_rounds_per_file`.
- Die Erfolgsdefinition wird maschinenlesbar ausgewertet als:
  - `criterion_no_new_batch_aborts`,
  - `criterion_no_accepted_regressions`,
  - `criterion_regression_set_improved`,
  - `criterion_stable_families_not_worse`,
  - sowie `overall_success` als zusammengefasster Abschlussstatus.

**Reproduzierbarer Aufruf:**
```bash
python -m src.image_composite_converter \
  artifacts/images_to_convert \
  --csv-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --ac08-regression-set \
  128
```

Danach liegen die schriftlich fixierten Erfolgskriterien und die aktuelle Bewertung im Report-Ordner unter `artifacts/converted_images/reports/`.

---

## Empfohlene Abarbeitungsreihenfolge

1. Aufgabe 1.1 – Qualitäts-Pass absichern
2. Aufgabe 1.2 – Stagnation erkennen
3. Aufgabe 1.3 – Render-/Batchfehler robust machen
4. Aufgabe 2.1 – Semantik-Audit für AC0811–AC0814
5. Aufgabe 2.2 – Prioritätsregeln der Family-Semantik festziehen
6. Aufgabe 3.1 – Adaptive Locks für Problemfamilien
7. Aufgabe 3.2 – `_S`-Varianten separat behandeln
8. Aufgabe 4.1 bis 4.4 – Familienweise Feinarbeit
9. Aufgabe 5.1 – Regression-Set fixieren
10. Aufgabe 5.2 – Erfolgskriterien dauerhaft dokumentieren

---

## Praktische Arbeitsweise pro Aufgabe

Für jede Aufgabe empfiehlt sich derselbe Ablauf:

1. kleine Codeänderung implementieren,
2. nur den relevanten AC08-Teilbatch laufen lassen,
3. Logs/CSV-Diffs sichern,
4. Verbesserung oder Regression kurz dokumentieren,
5. erst dann die nächste Aufgabe beginnen.

So bleibt jederzeit nachvollziehbar, welche Änderung welchen Effekt hatte.
