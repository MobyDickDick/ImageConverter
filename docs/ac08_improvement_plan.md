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

### Aufgabe 2.2 – Prioritätsregeln für Family-Semantik festziehen ✅ erledigt
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

**Umgesetzt in Code/Workflow:**
- `Reflection.parse_description` trennt jetzt Family-Regeln, Layout-Overrides und heuristische Beschreibungsauswertung explizit und speichert die feste Prioritätsreihenfolge `family_rule > layout_override > description_heuristic`.
- Für `AC0811..AC0814` werden widersprüchliche Text-Heuristiken (z. B. "`Kreis + Buchstabe CO_2`") nicht mehr in `params["elements"]` übernommen, wenn die Family-Regel "`Kreis ohne Buchstabe`" bereits feststeht.
- Konflikte zwischen Family-Regeln und weicheren Heuristiken werden in `semantic_conflicts` gesammelt und sowohl in den per-Datei-Logs als auch in den aggregierten Audit-Reports (`semantic_audit_ac0811_ac0814.csv/.json`) ausgegeben.

**Empfohlene Tests:**
- Direkter Vorher/Nachher-Vergleich der betroffenen Semantik-Fehler

---

## Phase 3 – Suchraum für Problemfamilien gezielt öffnen

### Aufgabe 3.1 – Adaptive Locks für AC08-Problemfälle ✅ erledigt
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

**Umgesetzt in Code/Workflow:**
- `Action._activate_ac08_adaptive_locks` öffnet bei Stagnation bzw. weiterhin hohem Fehler einen eng begrenzten Fallback-Suchraum nur für die dokumentierten Problemfamilien `AC0882`, `AC0837`, `AC0839`, `AC0820` und `AC0831`.
- Freigegeben werden dabei nur bounded Anpassungen: leicht erweiterte Radiusgrenzen (`min_circle_radius`/`max_circle_radius`), gelockerte Mindestlängen für Connectoren (`arm_len_min_ratio`/`stem_len_min_ratio`), bounded Textskalierung für kleine bzw. betroffene Text-Badges sowie eine enge Farbkorrektur innerhalb definierter Grauwert-Korridore.
- `validate_badge_by_elements` aktiviert diese Family-Unlocks explizit erst dann, wenn der normale Validierungspfad stagniert (`identical_fingerprint` bzw. `no_geometry_movement`) und schreibt dafür nachvollziehbare Logmarker wie `adaptive_unlock_applied` und den Wechsel in den Fallback-Search-Modus.
- Das Farb-Bracketing respektiert die neuen Min/Max-Korridore, damit adaptive Freigaben keine unkontrollierten Paletten-Regressionen erzeugen.

**Empfohlene Tests:**
- Fokus-Batch auf die Top-Ausreißer aus `pixel_delta2_ranking.csv`

---

### Aufgabe 3.2 – Separate Regeln für kleine Varianten (`_S`) ✅ erledigt
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

**Umgesetzt in Code/Workflow:**
- `Action._is_ac08_small_variant` und `Action._configure_ac08_small_variant_mode` klassifizieren jetzt `_S`-Badges über Variantensuffix und `min(width, height)` und aktivieren dafür einen expliziten `ac08_small_variant_mode` samt Metadaten.
- Der Small-Variant-Modus setzt eigene, eng begrenzte Textfenster für `CO₂`/`VOC`, reduziert den `CO₂`-Subscript-Offset bei kleinen Badges und hebt die Mindestlängen für Arm-/Stem-Connectoren an, damit `_S`-Varianten nicht zu kurzen Stummeln kollabieren.
- `extract_badge_element_mask` erweitert in diesem Modus die Foreground-Masken minimal per Dilation, und `Action._element_match_error` rechnet eine kleine Anti-Aliasing-Toleranz ein, damit winzige Badge-Kanten nicht übergewichtet werden.
- `validate_badge_by_elements` schreibt mit `small_variant_mode_active` einen expliziten Logmarker inklusive Grund, `min_dim`, Masken-Dilation und Connector-Floors, sodass Small-Variant-Läufe im Report direkt nachvollziehbar sind.

**Empfohlene Tests:**
- Nur `_S`-Varianten aller AC08-Familien in einem Sammelbatch

---

## Phase 4 – Familienweise Feinarbeit

### Aufgabe 4.1 – Linke Connector-Familien gemeinsam tunen ✅ erledigt
**Familien:** `AC0812`, `AC0832`, `AC0837`, `AC0882`

**Ziel:** Linksausrichtung, Arm-Länge und Kreisverankerung gemeinsam stabilisieren.

**Umgesetzt in Code/Workflow:**
- `Action._tune_ac08_left_connector_family` bündelt jetzt die gemeinsamen Guardrails für alle linken Connector-Familien und versieht sie mit der Familienmarkierung `connector_family_group=ac08_left_connector`.
- Die gemeinsame Familienlogik hält den Kreis auf dem semantischen Template-Zentrum (`lock_circle_cx/cy`), erzwingt einen robusten Mindestanteil für die linke Arm-Länge und begrenzt `max_circle_radius` zusätzlich über die verfügbare Connector-Spanne, damit der Kreis nicht in den Arm hineinwächst.
- Für Text-Varianten werden lesbare, zentrierte Textgrenzen mitgeführt: CO₂/VOC-Badges erhalten bounded Mindest-/Maximalskalen, und die `path_t`-Variante (`AC0882`) zentriert den Glyph-Bounding-Box-Anker nach dem Familien-Tuning erneut.
- Die bestehende Arm-Wiederherstellung über `Action._enforce_left_arm_badge_geometry` bleibt Bestandteil der Familienlogik, sodass fehlende oder temporär verlorene Connector-Geometrie vor der Finalisierung zuverlässig rekonstruiert wird.

**Prüfpunkte:**
- Arm bleibt sichtbar und ausreichend lang.
- Kreis kollabiert nicht in Richtung Connector.
- Text bleibt lesbar und zentriert.

**Empfohlene/ergänzte Tests:**
- Unit-Tests für `AC0832_S` prüfen die gemeinsamen Familien-Guardrails (Kreis-Locks, Connector-Längenfloor, Text-Skalierungsgrenzen und Radius-Obergrenze).
- Unit-Tests für `AC0882_L` prüfen, dass `path_t` zentriert bleibt und die linke Arm-Geometrie auch aus einem unvollständigen Paramatersatz wiederhergestellt wird.

---

### Aufgabe 4.2 – Rechte Connector-Familien gemeinsam tunen ✅ erledigt
**Familien:** `AC0810`, `AC0814`, `AC0833`, `AC0834`, `AC0838`, `AC0839`

**Ziel:** Spiegelbildliche Fälle konsistent behandeln.

**Umgesetzt in Code/Workflow:**
- `Action._tune_ac08_right_connector_family` bündelt jetzt die gemeinsamen Guardrails für alle rechten Connector-Familien und markiert sie mit `connector_family_group=ac08_right_connector`.
- Die gemeinsame Familienlogik spiegelt die linken Connector-Guardrails: Kreiszentrum bleibt über `template_circle_cx/cy` an der semantischen Vorlage verankert, der rechte Arm wird über `arm_len_min_ratio` bzw. `arm_len_min` sichtbar gehalten und `max_circle_radius` wird an die verbleibende rechte Connector-Spanne gekoppelt, damit der Kreis nicht in den Arm hineinwächst.
- `Action._enforce_right_arm_badge_geometry` stellt fehlende oder verloren gegangene Arm-Geometrie für `AC0810`, `AC0814`, `AC0833`, `AC0834`, `AC0838` und `AC0839` aus der finalen Kreispose wieder her; `_enforce_semantic_connector_expectation` nutzt diese Rekonstruktion jetzt auch bei semantisch erwarteten rechten Horizontalarmen.
- Für CO₂- und VOC-Varianten werden lesbare, begrenzte Textfenster mitgeführt (`co2_font_scale_*`, `voc_font_scale_*`), sodass kleine rechte Varianten nicht mehr unverhältnismäßig nach unten/rechts driften oder textseitig kollabieren.

**Prüfpunkte/ergänzte Tests:**
- Neue Tests für `AC0834_S` prüfen die gemeinsamen Guardrails der rechten Connector-Familie (Kreis-Locks, Arm-Rekonstruktion, Mindestarmverhältnis und CO₂-Textgrenzen).
- Neue Tests für `AC0839_L` prüfen, dass VOC-Varianten den rechten Arm sichtbar halten und bounded Textskalierung verwenden.

---

### Aufgabe 4.3 – Vertikale Connector-Familien gemeinsam tunen ✅ erledigt
**Familien:** `AC0811`, `AC0813`, `AC0831`, `AC0836`, `AC0881`

**Ziel:** Vertikale Stämme/Arme und Textlage robust auflösen.

**Umgesetzt in Code/Workflow:**
- `Action._tune_ac08_vertical_connector_family` bündelt jetzt gemeinsame Guardrails für `AC0811`, `AC0813`, `AC0831`, `AC0836` und `AC0881` und markiert sie mit `connector_family_group=ac08_vertical_connector`.
- Die Familienlogik verankert Kreiszentrum und vertikale Connector-Achse wieder an der semantischen Vorlage, rekonstruiert fehlende Stems/vertikale Arme über `Action._enforce_vertical_connector_badge_geometry` und erzwingt Mindestlängen über `stem_len_min_ratio` bzw. `arm_len_min_ratio`, damit vertikale Ausdehnung nicht kollabiert.
- CO₂-Varianten verwenden nun standardisiert cluster-zentrierte Textverankerung mit leichtem Down-Bias und bounded Textfenstern; VOC-Varianten behalten ebenfalls gebundene Skalierungsgrenzen, damit die Textlage in vertikalen Familien nicht top-heavy wird.

**Prüfpunkte/ergänzte Tests:**
- Neue Tests für `AC0831_L` prüfen die gemeinsamen Guardrails der vertikalen Connector-Familie (Kreis-Locks, Stem-Rekonstruktion, Mindest-Stemverhältnis und CO₂-Textlage).
- Neue Tests für `AC0836_L` prüfen, dass VOC-Varianten den Stem mittig zum Kreis halten und bounded Textskalierung verwenden.

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
