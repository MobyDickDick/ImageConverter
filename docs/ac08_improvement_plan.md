# AC08 improvement plan

Diese Datei ist der knappe Arbeitsplan zur aktuell eingecheckten AC08-Serie.
Die datenbasierte Analyse des derzeitigen Snapshots steht in
`docs/ac08_artifact_analysis.md`.

## Aktuelle Prioritäten

1. **Vertikale Anschlussfamilien stabilisieren**
   - Familien: `AC0811`, `AC0813`, `AC0831`, `AC0836`
   - Ziel: keine Fehlklassifikation mehr als `waagrechter Strich`

2. **Kreisdetektion für kleine Varianten absichern**
   - Varianten: `AC0811_S`, `AC0814_S`, `AC0870_S`
   - Ziel: Kreis-Fallback vor der Semantikprüfung zuverlässig machen

3. **Plain-Ring-Semantik für `AC0800` ergänzen**
   - Varianten: `AC0800_L`, `AC0800_M`, `AC0800_S`
   - Ziel: `Kreis ohne Buchstabe` explizit aus der Familienregel ableiten

4. **Reports nach der nächsten Runde neu erzeugen**
   - Ziel: aktualisierte Validierungslogs und bereinigtes Backlog

## Nächste Qualitätsstufe (familienübergreifende Harmonisierung)

Die bisherigen Regeln harmonisieren primär Varianten **innerhalb derselben Basis**
(`*_L`, `*_M`, `*_S`). Für die AC08-Serie ist als nächster Schritt zusätzlich eine
familienübergreifende Harmonisierung geplant, um gemeinsame Grundformen besser
auszunutzen:

1. **Skalen-Familien ohne Geometrieänderung**
   - Kandidaten: `AC0800_L/M/S`, `AC0820_L/M/S`
   - Ziel: identische Grundform + relative Textlage, nur Radius/Schriftgröße skaliert.

2. **Rotations-Familien mit gleicher Topologie**
   - Kandidaten: `AC0811..AC0814` jeweils `L/M/S`
   - Ziel: gleiche Topologie als kanonisches Proto-Modell behandeln und nur
     Rotations-/Spiegel-Transform anwenden.

3. **Alias-Familien mit statischer Beschriftungsorientierung**
   - Kandidaten: `AC0831..AC0834` jeweils `L/M/S` als visuelle Alias-Gruppe zu
     `AC0811..AC0814`
   - Ziel: Geometrie von der 081x-Gruppe übernehmen, Text aber nicht mitrotieren
     und separat in der Zielgröße re-fitten.

4. **Regressionstor für Familien-Konsistenz**
   - Ziel: neue Kennzahlen für Formähnlichkeit (normalisierte Geometriesignatur)
     und Textstabilität zwischen den genannten Familien in den Report aufnehmen.

## Erwartete Deliverables der nächsten Runde

- gezielte Algorithmusänderungen in der Primitive- und Kreis-Erkennung,
- zusätzliche Reportinstrumentierung für Anschlussrichtung und Kreisquelle,
- Regressionstests für die behobenen Familien,
- aktualisierte AC08-Reports und ein synchronisiertes `docs/open_tasks.md`.
