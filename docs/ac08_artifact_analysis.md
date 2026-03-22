# AC08 artifact analysis

Diese Notiz fasst den aktuell eingecheckten AC08-Report-Snapshot aus
`artifacts/converted_images/reports/AC08*_element_validation.log` zusammen und
übersetzt ihn in konkrete nächste Verbesserungsmaßnahmen.

## Snapshot-Zusammenfassung

Aus den aktuell vorhandenen AC08-Validierungslogs ergeben sich 54 ausgewertete
Varianten:

- `43` Fälle mit `status=semantic_ok`
- `11` Fälle mit `status=semantic_mismatch`

Die verbliebenen Mismatches clustern stark auf wenige Familien:

| Familie | Betroffene Varianten | Häufigste Beobachtung |
| --- | --- | --- |
| `AC0800` | `S` | Plain-Ring-Semantik ist vorhanden; für die kleine Variante bleibt die Radius-Stabilität der sensible Punkt |
| `AC0811` | `M`, `S` | Kreis + vertikaler Stiel werden falsch als waagrechter Strich bzw. fehlender Kreis bewertet |
| `AC0813` | `L`, `M` | Vertikaler Anschluss wird in der Validierung als waagrechter Strich fehlklassifiziert |
| `AC0814` | `S` | Kreisdetektion bricht im kleinen Raster zusammen |
| `AC0831` | `M` | CO₂-Variante mit vertikalem Anschluss wird als horizontaler Strich gelesen |
| `AC0836` | `L` | Vertikaler Anschluss wird als horizontaler Strich gelesen |
| `AC0870` | `S` | Kreisdetektion und primitive Segmentierung sind für kleine CO₂-Badges noch instabil |

## Dominante Fehlermuster

Die Reportdaten zeigen drei wiederkehrende Problemklassen:

1. **Kreis nicht robust erkannt**
   - Meldungen wie `Beschreibung erwartet Kreis, im Bild aber nicht robust erkennbar`
     und `Strukturprüfung: Kein belastbarer Kreis-Kandidat im Rohbild erkannt`.
   - Besonders sichtbar bei `AC0811_M`, `AC0811_S`, `AC0814_S` und `AC0870_S`.

2. **Vertikale Anschlüsse werden als horizontal interpretiert**
   - Meldung `Im Bild ist waagrechter Strich erkennbar, aber nicht in der Beschreibung enthalten`.
   - Betroffen sind vor allem `AC0811_*`, `AC0813_*`, `AC0831_M` und `AC0836_L`.
   - Das deutet eher auf ein Validierungs-/Primitiverkennungsproblem als auf ein
     reines SVG-Layoutproblem hin.

3. **Plain-circle-Familie `AC0800_S` bleibt geometrisch sensibel**
   - `AC0800_L` und `AC0800_M` gelten aktuell als optimal konvertiert und sollten
     nur noch regressionsgesichert mitlaufen.
   - Die kleine Variante ist weiterhin der empfindlichste Fall, weil ihr Kreis
     trotz korrekter Konzentrizität optisch zu klein werden kann, wenn die
     Radius-Optimierung unter die Template-Geometrie fällt.

## Empfohlene nächste Algorithmus-Maßnahmen

### 1. Kreis-Fallback für kleine AC08-Varianten ausbauen

Priorität: **hoch**

- Den lokalen Masken-/Foreground-Fallback, der bei `AC0800` bereits gegen dünne
  JPEG-Ringe hilft, gezielt für die kleinen Varianten `AC0811_S`, `AC0814_S` und
  `AC0870_S` nachschärfen.
- Die Schwellen für minimale Ring-Pixel, Bounding-Box-Fläche und Rundheitsprüfung
  für `_S`-Varianten separat instrumentieren, damit kleine Ringe nicht schon vor
  der Semantikprüfung ausgesiebt werden.
- Zusätzlich pro Fehlfall die Kreis-Kandidaten aus Rohbild vs. Foreground-Maske in
  den Report schreiben, damit der Unterschied zwischen Erkennungs- und
  Beschreibungsfehler sichtbar wird.

### 2. Primitive-Erkennung für vertikale Anschlussfamilien entkoppeln

Priorität: **hoch**

- Für die Familien `AC0811`, `AC0813`, `AC0831` und `AC0836` eine strengere
  Richtungslogik in der Primitive-Erkennung ergänzen: schmale, hohe Komponenten in
  Kreisnähe dürfen nicht mehr als generischer horizontaler Strich enden.
- Die Validierung sollte die Anschlussrichtung aus Familienregel + lokaler
  Komponentengeometrie gemeinsam ableiten, statt die globale Heuristik allein zu
  verwenden.
- Für diese Familien zusätzliche Debug-Marker in den Report aufnehmen, z. B.
  `primitive_arm_orientation=vertical|horizontal|ambiguous`.

### 3. Kleine `AC0800`-Variante geometrisch stabil halten

Priorität: **mittel**

- `AC0800_L` und `AC0800_M` als optimale Referenzvarianten beibehalten und bei
  künftigen AC08-Anpassungen immer mitprüfen.
- Für `AC0800_S` sicherstellen, dass die Kreis-Optimierung die Template-Radius-
  Untergrenze nicht unterschreitet, auch wenn Anti-Aliasing oder JPEG-Artefakte
  lokale Fehlerminima erzeugen.
- Die Plain-Ring-Familie weiterhin mit gezielten Regressionstests für `L/M/S`
  absichern.

### 4. CO₂-Kleinvarianten getrennt instrumentieren

Priorität: **mittel**

- `AC0870_S` nicht nur als Circle/Text-Fall betrachten, sondern die Kombination aus
  kleinem Ring und CO₂-Text separat protokollieren.
- Sinnvoll wären zusätzliche Reportfelder wie
  `text_cluster_bbox`, `circle_candidate_source`, `semantic_text_support_score`.

## Reihenfolge für die nächste Arbeitsrunde

1. Vertikal-vs.-horizontal-Fehlklassifikation (`AC0811`, `AC0813`, `AC0831`, `AC0836`)
2. Kreis-Fallback für `_S`-Varianten (`AC0811_S`, `AC0814_S`, `AC0870_S`)
3. Semantische Familienregel für `AC0800`
4. Danach AC08-Regression-Set und Report-Snapshot neu erzeugen

## Definition of done für den nächsten AC08-Zyklus

Die nächste Verbesserungsrunde sollte erst als abgeschlossen gelten, wenn:

- alle oben genannten Familien erneut konvertiert wurden,
- die betroffenen `*_element_validation.log`-Dateien keinen
  `semantic_mismatch` mehr enthalten oder bewusst begründete Restfälle benennen,
- die neue Reportinstrumentierung die Richtung der erkannten Anschlüsse und die
  Quelle des Kreis-Kandidaten sichtbar macht,
- die offenen Tasks in `docs/open_tasks.md` anschließend aktualisiert werden.
