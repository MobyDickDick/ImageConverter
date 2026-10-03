# Geplante Arbeitspakete: PNG + Beschreibung → SVG

Stand: 2026-10-03

Diese Pakete operationalisieren den Entwurf in
`docs/png_description_to_svg_implementation_blueprint.md`. Sie werden in der
angegebenen Reihenfolge bearbeitet. Jedes Paket ist klein genug für einen
eigenen Commit und darf erst als erledigt gelten, wenn sein maschinenlesbarer
Abnahmebeleg vorliegt.

## Gemeinsame Regeln

- Laufzeiteingaben sind genau Rasterbild und Beschreibung. Dateiname,
  früheres SVG, Sample-SVG, Bestliste und Template-Donor sind keine
  Wissensquellen.
- Jeder Lauf verwendet `semantic-only`, einen festen Seed und eine feste
  Toolchain. Zwischenartefakte dürfen beobachtet, aber nicht als Eingabe eines
  neuen Falls wiederverwendet werden.
- Bewertet wird immer das auf Platte gespeicherte SVG nach erneutem Rendern.
- Ein Exit-Code `0` bedeutet nur „Lauf technisch beendet“. Zufriedenheit wird
  ausschließlich durch das Good-Solution- und Quality-Complexity-Gate belegt.
- Es gibt kein weiteres Subpixel-/Antialiasing-Feintuning, solange Primitive,
  Beziehungen oder Z-Reihenfolge noch falsch sind.

## ZG7.1 – Echtes Zwei-Quellen-Fixture und Runner

**Status:** Abgeschlossen am 2026-10-03; Abnahmebeleg und Reproduktionsbefehl
stehen in `docs/next_arbeitspaket_2026-10-03_zg7_1.md`.

**Ziel:** Den bisherigen Description-Render-Smoke durch einen echten
End-to-End-Aufruf des `semantic-only`-Konverters ergänzen.

**Umfang**

- Drei kleine PNG-Fixtures für unterschiedliche Topologien: Kreis + Text +
  Anschluss, Rechteck + Diagonale, Polygonpfad + Linie.
- Pro Fixture eine eigenständige Beschreibung ohne Katalogkennung.
- Isoliertes Arbeitsverzeichnis pro Wiederholung; Resultat ist das tatsächlich
  vom Konverter geschriebene SVG.
- Der Runner verweigert fehlende Beschreibung, zusätzliches Referenz-SVG und
  nicht-semantic-only Ausführung.

**Deliverables**

- `config/semantic_only_png_benchmark_v1.json`
- Erweiterung von `tools/run_semantic_only_benchmark.py`
- Fixture-/CLI-Tests ohne Produktionsbild-ID

**Abnahme**

- Alle drei Fälle laufen dreimal bis zu einem parsebaren SVG.
- Input-Provenienz nennt ausschließlich PNG und Beschreibung.
- Umbenennung des PNGs ändert normalisierte Geometry-IR und SVG nicht.

## ZG7.2 – End-SVG-Metrikvertrag

**Abhängigkeit:** ZG7.1

**Status:** Abgeschlossen am 2026-10-03; Vertrag, Kalibrierung und Messbefund
stehen in `docs/next_arbeitspaket_2026-10-03_zg7_2.md`.

**Ziel:** Qualität statt bloßer Deterministik messen.

**Umfang**

- Gespeichertes SVG erneut rastern.
- `error_per_pixel`, Konturabstand/`edge_alignment`, Objektmasken-IoU,
  Anschlusskontinuität, `semantic_score` und `dimension_match` berechnen.
- Metriken je Objekt und für das Gesamtbild ausgeben; schlechteste Fehlerregion
  mit Bounding Box reporten.
- Nicht berechenbare Pflichtmetrik führt zu `not_reachable`, nicht zu `0` oder
  einem erfundenen Passwert.

**Deliverables**

- Versionierter Reportvertrag `semantic_only_quality_report_v1`
- fokussierte Metriktests mit perfekten und absichtlich falschen SVGs
- Reportartefakt für die drei ZG7.1-Fälle

**Abnahme**

- Ein synthetisches Referenz-SVG, aus dem das PNG-Fixture erzeugt wurde,
  erreicht für alle Metriken den Idealwert, ohne Raster einzubetten.
- Falsche Dimension, fehlendes Primitive und falscher Anschluss schlagen in
  jeweils der dafür vorgesehenen Metrik fehl.

## ZG7.3 – Constraint-Fusion und Hypothesen-Beam

**Abhängigkeit:** ZG7.2

**Status:** Abgeschlossen am 2026-10-03; Vertrag, Konfliktprotokoll und
Abnahmebeleg stehen in `docs/next_arbeitspaket_2026-10-03_zg7_3.md`.

**Ziel:** Beschreibung und Bildbefund gemeinsam zur richtigen Topologie führen.

**Umfang**

- Description-Constraints und Perception-Kandidaten über Primitive-Typ,
  relative Lage und Confidence zuordnen.
- Mindestens die besten drei zulässigen Geometry-IR-Hypothesen bis zur
  Bewertung behalten.
- Harte Constraints nie für einen reinen Pixelgewinn verletzen.
- Konflikte und verworfene Hypothesen mit Gründen protokollieren.

**Deliverables**

- versionierter `constraint_fusion_beam_v1`-Record
- Tests für mehrdeutigen Kreis/Rechteck-Befund, Anschlussrichtung und fehlendes
  Textsignal

**Abnahme**

- Umbenannte Fixtures liefern dieselbe Hypothesenreihenfolge.
- Ein pixelnäherer, aber semantisch falscher Kandidat kann nicht gewinnen.
- Unauflösbare Konflikte enden reproduzierbar mit `semantic_conflict`.

## ZG7.4 – Mehrzieloptimierung

**Abhängigkeit:** ZG7.3

**Status:** Abgeschlossen am 2026-10-03; Optimierungsvertrag,
Konvergenzprotokoll und Abnahmebeleg stehen in
`docs/next_arbeitspaket_2026-10-03_zg7_4.md`.

**Ziel:** Geometrie, Kontur, Farbe und Semantik verbessern, ohne die Topologie
zu beschädigen.

**Umfang**

- Diskrete Phase für Primitive-Zuordnung und Z-Order, anschließend
  kontinuierliche Phase für Position, Größe, Stroke, Farbe und Gradient.
- Zielfunktion aus Pixel-, Edge-, Struktur- und Semantikverlust.
- Grob-zu-feine Schritte, Trust-Region, festes Budget und Stagnationserkennung.
- Pro Iteration vollständige Komponenten und akzeptierte Änderung loggen.

**Deliverables**

- Konvergenz-CSV und maschinenlesbarer Optimierungsreport
- Regressionstest gegen Oszillation und semantische Regression

**Abnahme**

- Bei mindestens zwei der drei Fixtures sinkt der Gesamtverlust gegenüber der
  initialen Hypothese.
- Keine akzeptierte Iteration verschlechtert einen harten Constraint.
- Budgetüberschreitung und Stagnation besitzen kanonische Exit-/Reportgründe.

## ZG7.5 – Baseline und hartes Zufriedenheitsgate

**Abhängigkeit:** ZG7.4

**Ziel:** Eine Verbesserung und ein zufriedenstellendes Resultat getrennt und
ehrlich ausweisen.

**Umfang**

- Unveränderliche Baseline aus dem ersten vollständigen ZG7.4-Lauf speichern.
- Folgeergebnis je Metrik als `improved`, `unchanged` oder `regressed`
  klassifizieren.
- `satisfactory=true` nur setzen, wenn Good-Solution- und
  Quality-Complexity-Gate beide bestehen.
- Eingebettete Raster, falsche Dimensionen und semantisch falsche pixelnahe
  Resultate hart ablehnen.

**Deliverables**

- Baseline-Manifest mit Commit, Seed, Toolchain und Eingangs-Hashes
- Vorher-/Nachher-Report sowie Gateentscheidung pro Fall

**Abnahme**

- Keine Regression kann als zufriedenstellend akzeptiert werden.
- Wiederholung auf unverändertem Commit erzeugt identische Entscheidungen.
- Report trennt `technically_completed`, `improved` und `satisfactory`.

## ZG7.6 – Plan-B-Pilot ohne Sonderwissen

**Abhängigkeit:** ZG7.5

**Ziel:** Den neuen Pfad an einem echten, bislang unzufriedenstellenden
Plan-B-Fall prüfen, ohne dafür katalogspezifischen Code hinzuzufügen.

**Umfang**

- Mit dem obersten dann aktuellen Kandidaten aus `PLAN_B_KANDIDATEN.md`
  starten.
- Vorher-Baseline sichern, genau einen Algorithmus-/Primitive-Track bearbeiten
  und End-SVG erneut durch beide Gates schicken.
- Lerneffekt zusätzlich auf mindestens einem strukturell ähnlichen Holdout mit
  fremdem Namen prüfen.

**Abnahme**

- Der Pilot nennt konkrete Vorher-/Nachher-Werte.
- Ein positives Ergebnis gilt nur bei bestandenem Gate und nicht schlechterem
  Holdout.
- Andernfalls bleibt der Kandidat offen und der Report nennt die dominante
  Fehlerkomponente; es wird kein Erfolg aus einem bloßen Exit `0` abgeleitet.

## Reihenfolge und Entscheidungspunkte

`ZG7.1 → ZG7.2 → ZG7.3 → ZG7.4 → ZG7.5 → ZG7.6`

Nach ZG7.2 wird entschieden, welche Metrik den größten Abstand zeigt. Nach
ZG7.4 wird entschieden, ob weitere Optimierungsarbeit gerechtfertigt ist oder
ein Fall korrekt als `not_reachable` klassifiziert werden muss. Erst ZG7.5
erlaubt eine belastbare Aussage über Qualitätsverbesserung; erst ZG7.6 erlaubt
eine Aussage über den Nutzen für reale Plan-B-Fälle.
