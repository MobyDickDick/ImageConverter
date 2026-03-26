# Umsetzungscheck: Kelle-Modell und Suchstrategie

Dieser Check bewertet den Stand der Umsetzung für das gewünschte Vorgehen:

1. zusammenhängende Figur als Ganzes betrachten,
2. alle Parameter um ein Optimum gleichzeitig streuen,
3. Varianten prüfen,
4. Suchraum pro Parameter iterativ verengen,
5. einen stabilen Optimalbereich erkennen und daraus ein robustes Optimum ableiten.

## Kurzfazit

- **Kellen-Datenmodell (Kreis + Griff, Constraints, Clipping, Zeichenreihenfolge): weitgehend umgesetzt.**
- **Mehrdimensionale adaptive Suche mit iterativer Suchraum-Verengung: für die Kreis-Pose umgesetzt** (Adaptive-Domain-Suche inkl. Plateau-Auswertung).
- **Gleichzeitige Gesamtoptimierung aller Parameter einer Figur:** nur **teilweise** umgesetzt (voll für Kreis-Pose; weitere Parameter meist separat / schrittweise).
- **Explizite Schwerpunktberechnung eines multidimensionalen Maximum-Bereichs:** **nur angenähert** (Plateau-Mittelpunkt/Bounding-Box-Mitte, kein allgemeiner globaler Schwerpunkt über alle Parameter).

## Detailbewertung nach Wunschkriterien

### 1) „Ganze zusammenhängende Figur ermitteln und rekonstruieren"

**Umsetzung vorhanden (teilweise stark, teilweise spezialisiert):**

- Es gibt eine explizite Zerlegung/Erkennung für „Kreis + Stiel" als zusammenhängende Form (`decompose_circle_with_stem`), inkl. Richtungsableitung des Anschlusses.  
- Zusätzlich werden semantische Primitive (Kreis/Stiel/Arm/Text) im Gesamtbild geprüft und mit Familienregeln stabilisiert.

**Bewertung:** Für die relevanten Badge-Familien klar vorhanden; jedoch nicht als ein einziges generisches, formales Rekonstruktions-Framework für beliebige neue Symboltypen.

### 2) „Alle Parameter gleichzeitig um den optimalen Wert streuen"

**Teilweise umgesetzt:**

- Für die Kreisparameter `(cx, cy, r)` gibt es eine **mehrdimensionale** Stichprobensuche (`_optimize_circle_pose_adaptive_domain`), die pro Runde viele Kombinationen testet.
- Daneben existiert eine stochastische Survivor-Suche mit 3 Kandidaten pro Runde (`_optimize_circle_pose_stochastic_survivor`).
- Für einzelne Skalarparameter gibt es zusätzliche Survivor-Suchen (`_stochastic_survivor_scalar`).

**Bewertung:** Das „gleichzeitige Streuen" ist für die Kreis-Pose klar implementiert. Für alle anderen Parameter zusammen (Text, Stielbreite/-lage, Armgeometrie, Farben) erfolgt die Optimierung überwiegend elementweise/regelbasiert statt als ein gemeinsamer großer Suchvektor.

### 3) „Varianten überprüfen und Suchradius pro Parameter enger ziehen"

**Umsetzung klar vorhanden:**

- Adaptive-Domain-Suche verkleinert den 3D-Suchraum iterativ pro Runde (`shrink` + neue Grenzen für `cx/cy/r`).
- Stagnation wird erkannt (z. B. `stable_rounds`) und die Streuung reduziert.
- Protokollierung der eingegrenzten Möglichkeitsräume ist vorhanden.

**Bewertung:** Sehr nah an deiner Beschreibung — mindestens für die Kreis-Pose bereits exakt in diesem Muster umgesetzt.

### 4) „Multidimensionalen Bereich maximaler Approximation erkennen"

**Teilweise umgesetzt (für Kreis-Pose):**

- Es wird ein **Near-Optimum-Plateau** gebildet (`plateau`), nicht nur ein einzelner best point.
- Aus diesem Plateau werden Min/Max-Grenzen bestimmt; danach wird mit Plateau-Mitte und Bestpunkt gearbeitet.

**Bewertung:** Konzept ist vorhanden, aber aktuell domänenspezifisch (Kreis-Pose) und nicht als allgemeiner Optimierer über den gesamten Parameterraum.

### 5) „Schwerpunkt dieses Bereichs als Optimum verwenden"

**Teilweise umgesetzt / angenähert:**

- Es wird eine **Plateau-Mitte** als Surrogatkandidat verwendet (Mittelpunkt der Plateau-Bounding-Box), der gegen den Bestpunkt konkurriert.
- Eine echte Schwerpunkt-/Centroid-Berechnung über ein dichtes multidimensionales Maximum-Volumen ist nicht allgemein implementiert.

**Bewertung:** In die gewünschte Richtung vorhanden, aber noch nicht als vollständige Schwerpunkt-Methode über alle Modellparameter.

## Konkrete Lücken gegenüber deiner Zielvorstellung

1. **Globale Gleichzeitigkeit:**
   - Es fehlt ein einziger, gemeinsamer Optimierer über den kompletten Parametervektor (Kreis + Griff/Stiel/Arm + Text + Farben + ggf. Strichbreiten) mit einheitlicher Plateau-/Schwerpunktlogik.

2. **Allgemeiner Maximum-Bereich statt Spezialfall:**
   - Plateau-/Domain-Idee ist aktuell vor allem für die Kreis-Pose ausgebaut.

3. **Expliziter Schwerpunktoperator:**
   - Derzeit eher „Plateau-Mitte/Bestpunkt" statt eines robusten, gewichteten Schwerpunkts über den gesamten akzeptablen Hochgütebereich.

## Praktisches Ergebnis für deine Frage („inwieweit schon umgesetzt?“)

**Kurzantwort:**
- **Ja, der Kern deiner Suchidee ist bereits erkennbar umgesetzt — aber vor allem für die Kreis-Pose.**
- **Das volle Zielbild (ein einheitlicher, globaler Mehrparameter-Optimierer mit Schwerpunkt des Maximum-Bereichs) ist noch nicht vollständig umgesetzt.**


## Abgeleitete Aufgaben (umsetzbare Roadmap)

Die folgenden Aufgaben leiten sich direkt aus den identifizierten Lücken ab und sind so formuliert,
dass sie nacheinander abgearbeitet und getestet werden können.

### A1 – Gemeinsamen Parametervektor definieren
- [x] Einen einheitlichen Parametervektor für die Kelle/Badge-Geometrie einführen
      (mindestens: `cx`, `cy`, `r`, Griff-/Stiel-Lage, Griff-/Stiel-Breite, Textlage/Skalierung).
- [x] Pro Parameter klare Bounds und ggf. Locks dokumentieren (inkl. Herkunft: Template, Canvas, Semantik).
- [x] Bestehende elementweise Optimierer so kapseln, dass sie über denselben Vektor lesen/schreiben.

**Akzeptanzkriterium:** Es gibt eine zentrale Struktur, die alle optimierbaren Parameter enthält,
und eine Debug-Ausgabe, die den Vektor pro Runde protokolliert.

### A2 – Globale Mehrparameter-Suche ergänzen
- [ ] Einen globalen Optimierungsmodus implementieren, der nicht nur `(cx, cy, r)`, sondern mehrere
      Parameter gleichzeitig variiert.
- [ ] Sampling zunächst als robuste Baseline (z. B. zufällig/Gauß um aktuelles Bestes), mit
      schrittweise sinkender Streuung pro Runde.
- [ ] Fortschrittsmetrik pro Runde loggen (`best_err`, akzeptierte Kandidaten, verbesserte Parameter).

**Akzeptanzkriterium:** Mindestens ein reproduzierbarer Lauf optimiert >3 Parameter gleichzeitig
und liefert eine nachweisbare Fehlerverbesserung gegenüber dem Startzustand.

### A3 – Plateau/Maximum-Bereich verallgemeinern
- [ ] Plateau-Bildung aus der Circle-Pose-Suche auf den globalen Parameterraum übertragen.
- [ ] „Near-Optimum" formal definieren (`err <= best_err + epsilon`) und pro Runde persistieren.
- [ ] Plateau-Statistiken ausgeben (Anzahl Punkte, Spannweite je Parameter, Stabilitätsindikator).

**Akzeptanzkriterium:** Der Laufbericht enthält pro Runde einen expliziten Near-Optimum-Bereich
für den globalen Vektor, nicht nur für Kreisparameter.

### A4 – Schwerpunkt des Plateau-Bereichs berechnen
- [ ] Schwerpunktfunktion für das Plateau implementieren (ungewichtet oder fehlergewichtet).
- [ ] Schwerpunkt gegen „best sample" vergleichen und den robusteren Kandidaten übernehmen.
- [ ] Abbruch- und Sicherheitslogik definieren, falls Schwerpunkt außerhalb harter Constraints liegt.

**Akzeptanzkriterium:** Der finale Kandidat kann aus Schwerpunkt **oder** Bestpunkt stammen,
inklusive Begründung im Log.

### A5 – Regression und Qualitätssicherung
- [ ] Neue Tests für den globalen Suchmodus ergänzen (Determinismus via Seed, Constraint-Einhaltung,
      Verbesserung gegenüber Baseline).
- [ ] Bestehende Kelle-Tests beibehalten und um mindestens einen End-to-End-Fall mit aktivem
      globalen Suchmodus erweitern.
- [ ] Für AC08-/Kelle-relevante Familien einen kleinen Smoke-Regressionssatz definieren.

**Akzeptanzkriterium:** Testlauf zeigt, dass neue Suche stabil ist, Constraints nicht verletzt,
und keine bestehenden Kelle-/AC08-Baselines regressieren.

### Empfohlene Abarbeitungsreihenfolge
1. **A1** (Datenmodell vereinheitlichen)
2. **A2** (globale Suche lauffähig machen)
3. **A3** (Plateau verallgemeinern)
4. **A4** (Schwerpunktentscheidung)
5. **A5** (Tests + Regression-Gate)
