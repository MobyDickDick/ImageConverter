# Aufgaben: Bild + Beschreibung → SVG ohne Bildwissen im Runtime-Code

Diese Aufgaben operationalisieren die Zielarchitektur aus
`docs/image_description_only_architecture.md`. Sie sind absichtlich in kleine,
prüfbare Arbeitspakete zerlegt. Eine Aufgabe gilt erst dann als erledigt, wenn
ihre Akzeptanzkriterien automatisiert geprüft werden.

## Verbindliche Definition of Done

Für jedes Arbeitspaket gelten zusätzlich zu den jeweiligen Akzeptanzkriterien:

- keine neue Bild-/Katalog-ID in `src/`,
- keine Verlagerung konkreter Bildgeometrie in JSON, YAML oder Umgebungsvariablen,
- mindestens ein Test mit neutralem oder zufällig umbenanntem Dateinamen,
- Vergleich der SVG-Qualität vor und nach der Änderung,
- Verkleinerung der Legacy-Baseline, sobald ID-spezifischer Runtime-Code entfernt
  wurde.

## Priorität 0 – Generalisierung messbar und verbindlich machen

- [x] **IDO-01 – Dateinamen-Invarianztest einführen**
  - Aufgabe: Eine Eingabe unter mindestens zwei zufälligen, katalogfremden
    Dateinamen konvertieren und die SVG-Ergebnisse normalisiert vergleichen.
  - Zu ignorieren: Ausgabename, Zeitstempel und andere reine Metadaten.
  - Akzeptanz: Identische Pixel und identische Beschreibung erzeugen identische
    Geometry-IR und geometrisch äquivalente SVG-Ausgaben.
  - Umsetzung: Der Regressionstest führt dieselben synthetischen Pixel und
    dieselbe Beschreibung unter zwei deterministisch zufälligen, katalogfremden
    Namen durch den Non-Composite-Runtime-Pfad. Geometry-IR, kanonisiertes SVG,
    gerenderte Pixel und Fehlerwert müssen übereinstimmen. Gemeinsame
    Normalisierer entfernen ausschließlich Ausgabename und volatile Metadaten.

- [x] **IDO-02 – Runtime-Abhängigkeit von Bild-IDs instrumentieren**
  - Aufgabe: Alle Stellen protokollieren, an denen `base_name`, `variant_name`
    oder ein Dateistamm eine semantische oder geometrische Entscheidung
    beeinflusst.
  - Deliverable: Maschinenlesbarer Report mit Datei, Funktion, Entscheidungsart
    und aufgerufener Speziallogik.
  - Akzeptanz: Der Report unterscheidet legitime Verwendung als Ausgabename von
    verbotener Verwendung für Geometrie, Stil, Renderer- oder Optimiererwahl.
  - Umsetzung: `tools/report_runtime_image_id_dependencies.py` inventarisiert
    die Python-Runtime statisch per AST und schreibt Datei, Funktion, Zeilen,
    Entscheidungsart und aufgerufene Speziallogik als versionierten JSON-Report.
    Verzweigungen sowie Geometrie-/Stil-/Renderer-/Optimiereraufrufe werden als
    verbotene Runtime-Entscheidung, Ausgabe-/Reporting-Verwendungen als legitim
    und nicht eindeutig klassifizierbare Datenflüsse als prüfpflichtig markiert.

- [x] **IDO-03 – Hardcoding-Ratchet in den verbindlichen CI-Pfad aufnehmen**
  - Aufgabe: `tools/check_no_new_image_id_hardcoding.py` in den lokalen
    Completion-Check und den entsprechenden CI-Workflow integrieren.
  - Akzeptanz: Eine künstlich ergänzte Runtime-ID lässt den Check fehlschlagen;
    das Entfernen bestehender IDs bleibt erlaubt.
  - Umsetzung: Das lokale Abschlussprofil führt den Ratchet vor Compilation
    und Tests aus; GitHub Actions besitzt zusätzlich einen eigenständigen,
    verpflichtenden Ratchet-Job. Ein CLI-Negativtest scannt einen temporären
    Runtime-Quellbaum mit künstlicher ID und prüft den fehlschlagenden Exitcode.

- [x] **IDO-04 – Holdout- und Rename-Evaluationsprotokoll definieren**
  - Aufgabe: Trainings-/Entwicklungsbilder, Validierung und strikt
    zurückgehaltene Bilder trennen; Holdout-Dateien bei der Auswertung zufällig
    umbenennen.
  - Akzeptanz: Der Report weist Pixel-, Kanten-, Struktur- und Semantikmetriken
    getrennt für Entwicklungs- und Holdout-Satz aus.
  - Umsetzung: `tools/define_holdout_rename_protocol.py` schreibt den versionierten
    Report `artifacts/evaluation/holdout_rename_protocol_v1/holdout_rename_protocol_v1.json`
    mit Entwicklungs-/Holdout-Trennung, deterministischer katalogfreier
    Holdout-Umbenennung und verpflichtendem Pixel-, Kanten-, Struktur- und
    Semantikmetrikvertrag je Split; Regressionstests sichern die Umbenennung
    und das maschinenlesbare Reportformat ab.

## Priorität 1 – Beschreibung und Bild in eine gemeinsame Geometry-IR überführen

- [x] **IDO-05 – Bildunabhängiges Beschreibungsvokabular spezifizieren**
  - Aufgabe: Primitive, Richtungen, Relationen, Farben, Text/Glyphen,
    Überdeckungen und Negationen als versioniertes Schema definieren.
  - Beispiele: „Kreis“, „Linie links am Kreis“, „Text CO₂ im Kreis“,
    „ohne Beschriftung“.
  - Akzeptanz: Das Schema enthält keine Katalog-ID und kann Beschreibungen aus
    mindestens drei unterschiedlichen Symbolfamilien repräsentieren.
  - Umsetzung: `docs/vision/semantic_scene_description_v1.schema.json` definiert
    ein katalog-ID-freies Vokabular für Primitive, Richtungen, Relationen,
    Farben, Text/Glyphen, Überdeckungen, Negationen und Unsicherheiten.
    `artifacts/evaluation/semantic_scene_description_v1/description_vocabulary_examples.json`
    enthält prüfbare Beispiele für linken Kreis-Connector, Text-Badge und
    überdeckten Polygon-Pfeil.

- [x] **IDO-06 – Beschreibung ausschließlich in Constraints übersetzen**
  - Aufgabe: Den Parser so umbauen, dass er nur Geometry-IR-Elemente,
    Relationen und Unsicherheiten erzeugt, niemals einen katalogspezifischen
    Renderer auswählt.
  - Akzeptanz: Parser-Tests verwenden ausschließlich erfundene Namen; gleiche
    Beschreibung ergibt unabhängig vom Dateinamen die gleichen Constraints.
  - Umsetzung: `buildDescriptionConstraintsImpl(...)` erzeugt einen
    katalogfreien `description_geometry_constraints_v1`-Vertrag mit
    Geometry-IR-Elementen, Relationen und Unsicherheitsstatus.
    `Reflection.parse_description(...)` hängt diesen Vertrag zusätzlich an die
    Parser-Parameter; Regressionstests mit erfundenen Dateinamen sichern, dass
    gleiche Beschreibung identische Constraints ohne Renderer-/Mode-Auswahl und
    ohne Dateinamenspuren liefert.

- [x] **IDO-07 – Perception-Kandidaten vollständig auf dieselbe IR abbilden**
  - Aufgabe: Kreis/Ring, Linie, Rechteck, Polygon/Pfad, Textbereich und Farbe mit
    Confidence und Evidenz in die gemeinsame Geometry-IR überführen.
  - Akzeptanz: Jeder unterstützte Primitive-Typ besitzt mindestens einen
    synthetischen Detektions-, Serialisierungs- und Render-Roundtrip-Test.
  - Umsetzung: `merge_perception_candidates_into_geometry_ir(...)` mappt den
    stabilen `perception_primitive_candidate_v1`-Contract jetzt für Kreis/Ring,
    Linie, Rechteck, Polygon/Pfad, Text-Glyph/Textbereich und Farbfeld in
    Geometry-IR-Elemente mit Confidence-/Evidence-Metadaten. Der Renderer
    unterstützt dafür zusätzlich generische `PolygonPath`- und `ColorPatch`-
    Elemente. Synthetische Roundtrip-Regressionen prüfen Serialisierung,
    Geometry-IR-Seed und SVG-Renderbarkeit für jeden unterstützten
    Primitive-Typ.

- [x] **IDO-08 – Generische Fusionslogik implementieren**
  - Aufgabe: Bildkandidaten und Beschreibungs-Constraints über gewichtete Kosten
    beziehungsweise Wahrscheinlichkeiten zusammenführen.
  - Akzeptanz: Tests decken Übereinstimmung, fehlende Bildevidenz,
    widersprüchliche Beschreibung und mehrere plausible Kandidaten ab.
  - Umsetzung: `fuse_description_constraints_with_perception_candidates(...)`
    führt Beschreibungselemente und neutrale Perception-Kandidaten über
    Primitive-Kompatibilität, Confidence und optionale Bounding-Box-Überlappung
    in einem katalogfreien `description_perception_fusion_v1`-Vertrag zusammen.
    Der Entscheidungs-Trace unterscheidet `matched`, `missing_image_evidence`,
    `contradiction` und `ambiguous`; Regressionstests decken genau diese vier
    Akzeptanzfälle mit neutralen synthetischen Kandidaten ab.

- [x] **IDO-09 – Unsicherheitsvertrag definieren**
  - Aufgabe: Status, Gründe und Confidence für unzureichende oder
    widersprüchliche Evidenz festlegen.
  - Akzeptanz: Der Konverter halluziniert in Negativtests keine sichere
    Geometrie, sondern liefert einen maschinenlesbaren Review-/Unsicherheitsstatus.
  - Umsetzung: Die Fusionslogik erzeugt einen `fusion_uncertainty_v1`-Vertrag
    mit Status, Grund, betroffenen Constraint-Zielen, Confidence und
    `review_required`; `safe_geometry_ir` enthält nur eindeutig gematchte
    Geometrie. Negativtests sichern fehlende Bildevidenz und widersprüchliche
    Evidenz gegen sichere Geometrie-Halluzination ab.

## Priorität 2 – ID-spezifische Pfade schrittweise ersetzen

- [ ] **IDO-10 – Linker Kreis-Connector als erstes vertikales Migrationspaket**
  - Aufgabe: Alle ID-Listen für „Kreis mit linkem horizontalem Anschluss“ durch
    messbare Kreis-, Linien-, Kontakt- und Beschreibungseigenschaften ersetzen.
  - Akzeptanz: Umbenennungstests sind grün; bestehende Qualitätsfixtures
    regressieren nicht über die festgelegte Toleranz; zugehörige
    Baseline-Einträge sinken.
  - Fortschritt: Der erste katalogfreie Beschreibungspfad erzeugt für „Kreis
    mit waagrechtem Strich links vom Kreis“ eine `CircleBackground` +
    `HorizontalRule`-Geometry-IR mit `left_of`-Relation. Ein neutraler
    Rename-Test sichert, dass diese Beschreibung unabhängig vom Dateinamen
    dieselben Constraints und dieselbe Geometry-IR liefert. Run QC erweitert
    den Constraint-Vertrag um die explizite `left_of`-Relation und erkennt
    relationale Texte wie „Linie links vom Kreis“ ohne Familien-ID-Liste. Run
    QD ergänzt synonyme und inverse Relationsformulierungen wie „links neben
    dem Kreis“, „linker Anschluss“ und „Kreis rechts von der Linie“. Run QE
    reduziert die IDO-10-Legacy-Baseline weiter, indem Connector-Guards,
    Transfer-Kommentare und Validierungslogs linke/rechte Horizontalarme über
    Parameter und Richtung statt über konkrete Katalogfamilien dokumentieren.

- [ ] **IDO-11 – Rechter Kreis-Connector generalisieren**
  - Aufgabe: Spiegelung nicht über Familiennamen, sondern über erkannte
    Anschlussrichtung und Relationen modellieren.
  - Akzeptanz: Ein gemeinsamer Algorithmus verarbeitet linke und rechte
    Varianten; keine getrennten Bild-ID-Mengen bleiben in diesem Dispatch.

- [ ] **IDO-12 – Vertikale Kreis-Connectoren generalisieren**
  - Aufgabe: Obere und untere Anschlüsse anhand von Bildgeometrie,
    Überdeckung/Z-Order und Beschreibung unterscheiden.
  - Akzeptanz: Tests umfassen Anschluss oben, Anschluss unten, teilweise
    verdeckten Anschluss und connector-freien Kreis.

- [ ] **IDO-13 – Kreis-/Text-Badges generalisieren**
  - Aufgabe: Labelinhalt, Textlage und Kreisgeometrie aus Beschreibung,
    Text-/Glyph-Evidenz und Bildmessung bestimmen.
  - Akzeptanz: `T`, `M`, `VOC`, `CO₂`, `rF` und „ohne Buchstabe“ werden ohne
    Bild-ID-Dispatch verarbeitet.

- [ ] **IDO-14 – Ventil-/Kellen-Spezialpfade in Primitive zerlegen**
  - Aufgabe: Bisherige Spezialformen als Polygon-, Kreis-, Linien-,
    Symmetrie- und Rotationsrelationen ausdrücken.
  - Akzeptanz: Rotation und Spiegelung sind generische IR-Transformationen und
    keine katalogspezifischen Funktionen.

- [ ] **IDO-15 – Adaptive Locks und Optimierungsprofile entkoppeln**
  - Aufgabe: Profilwahl ausschließlich aus messbaren Eigenschaften wie
    Objektgröße, Connector-Richtung, Textdichte, Kontrast und
    Konvergenzverhalten ableiten.
  - Akzeptanz: Keine Bild-ID wählt Radius-, Farb-, Text- oder Connector-Limits.

## Priorität 3 – Konfiguration und Runtime bereinigen

- [ ] **IDO-16 – Globale Konfiguration v1 einführen**
  - Aufgabe: Ein kleines versioniertes JSON-Schema für globale
    Primitive-Schwellen, Kostenfunktionsgewichte, Budgets und
    Unsicherheitsgrenzen erstellen.
  - Akzeptanz: Schema-Validierung lehnt unbekannte Schlüssel und alle
    bildbezogenen Bereiche ab; Standardwerte reproduzieren das Verhalten ohne
    lokale Konfigurationsdatei.

- [ ] **IDO-17 – Runtime-Code von Katalog-IDs befreien**
  - Aufgabe: Nach Abschluss der vertikalen Migrationspakete verbleibende
    Bild-IDs aus `src/` entfernen oder auf reine Reporting-/Testdaten außerhalb
    der Runtime verschieben.
  - Akzeptanz: `tools/check_no_new_image_id_hardcoding.py` meldet für `src/`
    exakt `0` Vorkommen.

- [ ] **IDO-18 – Legacy-Baseline und Ratchet entfernen**
  - Voraussetzung: IDO-17 ist abgeschlossen.
  - Aufgabe: Die temporäre Legacy-Inventur durch eine absolute
    Null-Vorkommen-Regel ersetzen.
  - Akzeptanz: `config/legacy_image_id_baseline.json` ist gelöscht; der Check
    benötigt keine Allowlist und verbietet jede Bild-ID in Runtime-Quellen.

## Priorität 4 – Zielqualität nachweisen

- [ ] **IDO-19 – Ablationsmatrix automatisieren**
  - Aufgabe: Für denselben Holdout-Satz die Modi „nur Bild“, „nur
    Beschreibung“ und „Bild + Beschreibung“ auswerten.
  - Akzeptanz: Der kombinierte Modus verbessert die definierte Gesamtmetrik und
    der Report zeigt, welche Quelle welche Constraints beigetragen hat.

- [ ] **IDO-20 – Qualitäts- und Komplexitätsgate definieren**
  - Aufgabe: Rasterähnlichkeit, Kantenlage, Struktur, Semantik,
    SVG-Elementanzahl und Pfadkomplexität in einem Gate kombinieren.
  - Akzeptanz: Pixelkopien als eingebettetes Raster, unnötig komplexe Pfade und
    semantisch falsche, aber pixelnahe Ergebnisse werden abgelehnt.

- [ ] **IDO-21 – End-to-End-Holdout-Abnahme durchführen**
  - Voraussetzung: IDO-01 bis IDO-20 sind abgeschlossen.
  - Aufgabe: Einen nie zur Implementierung verwendeten Satz technischer Symbole
    ausschließlich aus Bild und Beschreibung konvertieren.
  - Akzeptanz: Kein Holdout-Name kommt in Runtime oder Konfiguration vor;
    Rename-Invarianz, Qualitätsgate und Unsicherheitskalibrierung bestehen.

## Empfohlene Ausführungsreihenfolge

1. IDO-01 bis IDO-04,
2. IDO-05 bis IDO-09,
3. IDO-10 als Referenzmigration,
4. IDO-11 bis IDO-15,
5. IDO-16 und IDO-17,
6. IDO-18 bis IDO-21.

IDO-10 sollte bewusst als erstes vollständiges vertikales Paket umgesetzt werden:
vom Beschreibungssignal und den Bilddetektoren über Fusion und Geometry-IR bis
zum SVG, Rename-Test und Abbau der Legacy-Baseline. Erst danach sollten weitere
Familien parallel migriert werden.
