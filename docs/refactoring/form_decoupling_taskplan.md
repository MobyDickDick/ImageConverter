# Aufgabenplan: Entkopplung der Formen vom Konvertierungsprogramm

## Zielbild
Das Konvertierungsprogramm darf **keine form-spezifischen Regeln** mehr enthalten (z. B. `AC0800_L`-Sonderlogik). Es arbeitet nur noch auf Basis einer externen Umsetzungsbeschreibung mit optimierbaren Parametern.

## Ergebnis-Artefakte
1. **Sprachbeschreibung** je Form (fachliche Beschreibung, ohne Algorithmik).
2. **Umsetzungsbeschreibung** je Form (Geometrie-/Farbprimitive + Parameterraum).
3. **Generischer Konvertierungsalgorithmus** (ohne Formwissen):
   - Parameter variieren
   - Rendern
   - Vergleichen
   - Parameterraum einengen
4. **Fehlschlag-Analysebericht** je entfernte Form inkl. Algorithmus-Verbesserungsvorschlag.

---

## Arbeitspaket A – Vollständige Bestandsaufnahme der Formabhängigkeiten

### A1. Formcodes im Code inventarisieren
- [ ] Alle harten Formreferenzen (`ACxxxx`, `GExxxx`, `ARxxxx`, etc.) im Runtime-Code auflisten.
- [ ] Treffer kategorisieren:
  - **erlaubt**: Daten-/Beschreibungsdateien
  - **nicht erlaubt**: Konvertierungs-/Optimierungslogik
- [ ] Ergebnis als CSV ablegen: `artifacts/reports/form_code_inventory.csv`

### A2. Module mit implizitem Formwissen markieren
- [ ] Prüfen und klassifizieren (Startliste):
  - `src/iCCModules/imageCompositeConverterSemantic*.py`
  - `src/iCCModules/imageCompositeConverterAc08Gate.py`
  - `src/iCCModules/imageCompositeConverterForms.py`
  - `src/iCCModules/imageCompositeConverterFormsSymmetricChords.py`
  - `src/iCCModules/imageCompositeConverterDualArrow*.py`
  - `src/iCCModules/imageCompositeConverterRemaining.py`
  - `src/imageCompositeConverter.py`
- [ ] Für jedes Modul dokumentieren:
  - Welche Formkenntnis eingebaut ist
  - Warum sie aktuell benötigt wird
  - In welches Datenmodell sie verschoben wird

### A3. Baseline-Qualität einfrieren
- [ ] Referenzlauf für alle bisher bekannten Formen durchführen.
- [ ] Metriken sichern (z. B. Score, Pixel-Diff, Erfolg/Fehlschlag, Laufzeit).
- [ ] Baseline-Bericht ablegen: `artifacts/reports/form_decoupling_baseline_YYYY-MM-DD.md`

---

## Arbeitspaket B – Ziel-Datenmodell für Umsetzungsbeschreibungen

### B1. Schema definieren
- [ ] Einheitliches Schema für Formumsetzung festlegen (JSON/YAML):
  - `shape_type` (z. B. circle, line, polygon, arrow, badge)
  - `parameters` (Name, Typ, Min/Max, Schrittweite/Prior)
  - `constraints` (z. B. Symmetrie, Achsenbindung)
  - `style_layers` (z. B. Rand/Hintergrund, Füllung)
  - `objective_weights` (Form-, Farb-, Kanten-Fehler)
- [ ] Validierungsregeln festlegen (Pflichtfelder, Wertebereiche).

### B2. Beispielmigration AC0800_L
- [ ] AC0800_L als Referenzfall anlegen:
  - Kreis
  - Rand dunkel
  - Hintergrund hell
  - Parameter: Mittelpunkt, Radius, Randbreite, Randfarbe, Hintergrundfarbe
- [ ] Sicherstellen, dass die Konvertierung **nur** aus dieser Beschreibung gespeist wird.

### B3. Beschreibungsspeicher aufbauen
- [ ] Ablagestruktur festlegen, z. B. `artifacts/descriptions/implementations/<FORM>.yaml`
- [ ] Loader + Schema-Validator integrieren.

---

## Arbeitspaket C – Formwissen aus dem Konverter entfernen (iterativ je Formfamilie)

### C1. Priorisierte Reihenfolge
- [ ] Familie 1: einfache Kreis-/Ringformen (z. B. AC08xx-Basis)
- [ ] Familie 2: Pfeile/Badges
- [ ] Familie 3: Mehrkomponentenformen
- [ ] Familie 4: Sonderfälle/Legacy

### C2. Iterationsschritt je Form
Für **jede** Form/Familie exakt dieses Vorgehen:
1. [ ] Form-spezifische Logik im Konverter identifizieren.
2. [ ] In Umsetzungsbeschreibung überführen.
3. [ ] Sonderlogik im Konverter entfernen.
4. [ ] Regression gegen Baseline fahren.
5. [ ] Fehlschläge analysieren und dokumentieren.
6. [ ] Algorithmus generisch verbessern (ohne neue Form-Sonderfälle).
7. [ ] Verbesserung auf bereits migrierte Formen gegenprüfen.

### C3. Verbotene Rückfälle absichern
- [ ] CI-Regel: neue form-spezifische `if form == ...` in Runtime-Modulen blockieren.
- [ ] Lint-Check für harte Formcodes außerhalb erlaubter Datenpfade.

---

## Arbeitspaket D – Fehlschlaganalyse & algorithmische Verbesserung

### D1. Standardisierte Fehlerklassen
- [ ] Suchraum zu eng/zu weit
- [ ] Falsche Initialisierung
- [ ] Nicht identifizierbare Kanten/Farben
- [ ] Topologiefehler (falsche Primitive)
- [ ] Lokales Minimum/instabile Optimierung

### D2. Verbesserungs-Backlog (generisch)
- [ ] Bessere Initialisierung (multi-start, coarse-to-fine)
- [ ] Adaptive Schrittweiten / Bayesian/TPE-ähnliche Suche
- [ ] Robustere Metrik-Kombination (Kanten + Farbe + Form)
- [ ] Dynamische Gewichtung nach Konfidenz
- [ ] Frühabbruch/Restart-Strategien

### D3. Pflichtartefakt je fehlgeschlagener Form
- [ ] Datei: `artifacts/reports/failure_analysis/<FORM>.md`
- [ ] Inhalte:
  - Symptom
  - Reproduktionskommando
  - Metriken vorher/nachher
  - Root Cause
  - Generische Verbesserung
  - Nebeneffekte auf andere Formen

---

## Arbeitspaket E – Abschlusskriterien

- [ ] Im Konvertierungsprogramm existiert keine Form-Sonderlogik mehr.
- [ ] Jede Form ist über Umsetzungsbeschreibung + Parameterraum modelliert.
- [ ] Qualitätsziel: keine signifikante Verschlechterung gegenüber Baseline.
- [ ] Für verbleibende Fehlschläge existiert ein priorisiertes, generisches Verbesserungs-Backlog.

---

## Konkrete nächste 10 Tasks (umsetzungsbereit)
1. [ ] `form_code_inventory.csv` automatisch erzeugen.
2. [ ] Runtime-Module in "erlaubt/nicht erlaubt" markieren.
3. [ ] Schema v1 für Umsetzungsbeschreibungen festschreiben.
4. [ ] Loader + Schema-Validierung implementieren.
5. [ ] AC0800_L vollständig auf datengetriebene Umsetzung migrieren.
6. [ ] AC0800_L-Sonderlogik im Konverter löschen.
7. [ ] Vollen Regressionstestlauf starten und Baseline vergleichen.
8. [ ] Fehlschlaganalyse für neu fehlgeschlagene Formen dokumentieren.
9. [ ] Erste generische Optimierungsverbesserung implementieren.
10. [ ] CI-Guard gegen neue form-spezifische Runtime-Branches einführen.
