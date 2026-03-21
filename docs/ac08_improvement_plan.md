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

## Erwartete Deliverables der nächsten Runde

- gezielte Algorithmusänderungen in der Primitive- und Kreis-Erkennung,
- zusätzliche Reportinstrumentierung für Anschlussrichtung und Kreisquelle,
- Regressionstests für die behobenen Familien,
- aktualisierte AC08-Reports und ein synchronisiertes `docs/open_tasks.md`.
