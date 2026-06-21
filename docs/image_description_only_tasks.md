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
    Parameter und Richtung statt über konkrete Katalogfamilien dokumentieren. Run
    QF bündelt die verbleibenden linken AC08-Connector-Branches in einem
    gemeinsamen `connector_direction=left`-Finalisierungspfad, sodass
    Enforcement und Fit-Dispatch über gerichtete Parameter statt duplizierte
    Familienzweige laufen; der Ratchet sinkt weiter auf 379 Runtime-ID-Vorkommen.

- [ ] **IDO-11 – Rechter Kreis-Connector generalisieren**
  - Aufgabe: Spiegelung nicht über Familiennamen, sondern über erkannte
    Anschlussrichtung und Relationen modellieren.
  - Akzeptanz: Ein gemeinsamer Algorithmus verarbeitet linke und rechte
    Varianten; keine getrennten Bild-ID-Mengen bleiben in diesem Dispatch.
  - Fortschritt: Run QG erweitert den in IDO-10 eingeführten gemeinsamen
    Horizontalarm-Finalisierungspfad auf `connector_direction=right`. Die
    rechten AC08-Varianten für einfache, CO₂-, VOC- und rF-Badges setzen ihre
    Richtung nun vor/nach optionalem Bild-Fit über denselben Parameterpfad und
    laufen durch die gemeinsame rechte Arm-Enforcement-Callback-Schnittstelle;
    der Ratchet sinkt auf 374 Runtime-ID-Vorkommen. Run QH spiegelt die
    rechten Relationsformulierungen im katalogfreien Beschreibungspfad: Texte
    wie „Linie rechts vom Kreis“, „rechter Anschluss“ und „Kreis links von der
    Linie“ erzeugen `CircleBackground` + `HorizontalRule` mit `right_of`-Relation
    und werden durch neutrale Rename-Tests abgesichert. Run QI entfernt die
    rF-Rechtsconnector-Folgepunkte aus der verbliebenen Familien-ID-Liste für
    rechte Horizontalarme; `AC0844`/`AC0864` erhalten ihren rechten Anschluss nun
    aus der Beschreibung-Heuristik, und der Ratchet sinkt auf 372
    Runtime-ID-Vorkommen. Run QJ entfernt auch die verbleibenden rechten
    Basis-/CO₂-/VOC-Familienanker `AC0810`, `AC0814`, `AC0834` und `AC0839`
    aus der expliziten rechten Connector-Liste; knappe Beschreibungen wie
    „Griff unten“ und „gegenüberliegende Drehlage“ liefern den rechten
    Horizontalarm nun über `description_heuristic`, und der Ratchet sinkt auf
    368 Runtime-ID-Vorkommen.

- [ ] **IDO-12 – Vertikale Kreis-Connectoren generalisieren**
  - Aufgabe: Obere und untere Anschlüsse anhand von Bildgeometrie,
    Überdeckung/Z-Order und Beschreibung unterscheiden.
  - Akzeptanz: Tests umfassen Anschluss oben, Anschluss unten, teilweise
    verdeckten Anschluss und connector-freien Kreis.
  - Fortschritt: Run QK startet den katalogfreien Vertikalpfad: Beschreibungen
    mit oberer/unterer Anschlusslinie erzeugen jetzt `CircleBackground` +
    `VerticalRule` mit `top_of`-/`bottom_of`-Relation. Neutrale Rename-Tests
    sichern Dateinamen-Invarianz; Semantik-Heuristiktests leiten obere und
    untere Connectoren aus Relationsformulierungen statt aus neuen
    Familien-ID-Regeln ab. Run QL ergänzt teilverdeckte obere/untere Anschlüsse
    mit `z_order=behind_target` und `continues_behind`-Relation sowie
    connector-freie Kreis-Negativtests mit `connector_policy=forbid`.

- [ ] **IDO-13 – Kreis-/Text-Badges generalisieren**
  - Aufgabe: Labelinhalt, Textlage und Kreisgeometrie aus Beschreibung,
    Text-/Glyph-Evidenz und Bildmessung bestimmen.
  - Akzeptanz: `T`, `M`, `VOC`, `CO₂`, `rF` und „ohne Buchstabe“ werden ohne
    Bild-ID-Dispatch verarbeitet.
  - Fortschritt: Run QM startet den katalogfreien Badge-Pfad: Labeltexte für
    `T`, `M`, `VOC`, `CO₂`, `rF`/`rH` sowie textfreie Kreisformulierungen werden
    aus der Beschreibung in `CircleBackground`-/`TextGlyph`-IR übersetzt.
    Zentrierte Textlage wird als `centered_in`-Relation modelliert; kleine und
    große Kreisformulierungen setzen generische Badge-Bounding-Boxes, und
    connector-freie textlose Kreise behalten `connector_policy=forbid`.

- [ ] **IDO-14 – Ventil-/Kellen-Spezialpfade in Primitive zerlegen**
  - Aufgabe: Bisherige Spezialformen als Polygon-, Kreis-, Linien-,
    Symmetrie- und Rotationsrelationen ausdrücken.
  - Akzeptanz: Rotation und Spiegelung sind generische IR-Transformationen und
    keine katalogspezifischen Funktionen.
  - Fortschritt: Run QO startet den Primitive-/Transformationsvertrag für
    Top-Kellen-/3-Wege-Ventile: Die Geometry-IR enthält nun eine
    `primitive_decomposition` aus Polygonkörper, Kreisgriff, Linien-Connector
    und optionalem Text-Glyph sowie einen generischen `transform`-Block für
    Rotation beziehungsweise Spiegelung. Ein neutraler, katalogfreier
    Description-Test sichert die 180°-Rotation ohne neue Bild-ID-Regel ab. Run QP
    erweitert denselben Vertrag auf vertikale 2-Wege-Motorventile: Die
    Geometry-IR beschreibt nun zwei Polygonhälften, Kreisgriff, Linien-Connector
    und Motor-Text sowie generische Rotationen für neutrale Beschreibungen.

- [ ] **IDO-15 – Adaptive Locks und Optimierungsprofile entkoppeln**
  - Aufgabe: Profilwahl ausschließlich aus messbaren Eigenschaften wie
    Objektgröße, Connector-Richtung, Textdichte, Kontrast und
    Konvergenzverhalten ableiten.
  - Akzeptanz: Keine Bild-ID wählt Radius-, Farb-, Text- oder Connector-Limits.
  - Fortschritt: Run QQ ergänzt einen katalogfreien `optimization_profile=unrestricted`-
    Eingang für die globalen Optimierungsgrenzen. Der bisherige AC0811-
    Kompatibilitätsflag bleibt als Alias erhalten, aber neue neutrale Tests
    sichern, dass Radius-, Text- und Connector-Locks ohne Bild-ID über
    Profilmetadaten entsperrt werden können.

## Priorität 3 – Konfiguration und Runtime bereinigen

- [ ] **IDO-16 – Globale Konfiguration v1 einführen**
  - Aufgabe: Ein kleines versioniertes JSON-Schema für globale
    Primitive-Schwellen, Kostenfunktionsgewichte, Budgets und
    Unsicherheitsgrenzen erstellen.
  - Akzeptanz: Schema-Validierung lehnt unbekannte Schlüssel und alle
    bildbezogenen Bereiche ab; Standardwerte reproduzieren das Verhalten ohne
    lokale Konfigurationsdatei.
  - Fortschritt: Run QR führt `global_converter_config_v1` als katalogfreie
    globale Konfiguration ein. Schema und versionierte Default-Datei enthalten
    ausschließlich Primitive-Schwellen, Kostenfunktionsgewichte, Budgets und
    Unsicherheitsgrenzen; Loader-/Validator-Tests sichern Defaults, Fallback
    sowie die Ablehnung unbekannter und bildbezogener Konfigurationsbereiche.

- [ ] **IDO-17 – Runtime-Code von Katalog-IDs befreien**
  - Aufgabe: Nach Abschluss der vertikalen Migrationspakete verbleibende
    Bild-IDs aus `src/` entfernen oder auf reine Reporting-/Testdaten außerhalb
    der Runtime verschieben.
  - Akzeptanz: `tools/check_no_new_image_id_hardcoding.py` meldet für `src/`
    exakt `0` Vorkommen.
  - Fortschritt: Run QS entkoppelt die AC08-Adaptive-Unlock-Auswahl von
    expliziten Familienlisten. Die Aktivierung läuft jetzt über generische
    Parameter (`enable_adaptive_unlock`, `adaptive_unlock_min_error`), die aus
    Text-/Connector-Merkmalen der finalisierten Badge-IR abgeleitet werden; ein
    neutraler Rename-/Katalog-fremder Test sichert den geometriebasierten Pfad.
    Der Ratchet sinkt von 367 auf 362 Runtime-ID-Vorkommen. Run QT entfernt die
    AC08-Small-Circle-Fallback-Familienliste aus der semantischen
    Primitive-Erkennung: Der Rescue-Pfad hängt jetzt nur noch an
    `ac08_small_variant_mode`, aktivierter Kreisgeometrie und einer endlichen
    erwarteten Kreis-Schätzung. Ein neutraler synthetischer Small-Ring-Test
    sichert den katalognamenfreien Pfad; der Ratchet sinkt weiter auf 335
    Runtime-ID-Vorkommen. Run QU entkoppelt die Plain-Ring-Erhaltung im
    Finalisierungs- und SVG-Pfad von `AC0800`-Namensguards: Der Pfad hängt nun
    an `preserve_plain_ring_geometry`/`plain_ring_geometry`, ein neutraler
    `AC08XX_RING`-Test sichert die parameterbasierte Auswahl, und der Ratchet
    sinkt auf 331 Runtime-ID-Vorkommen. Run QV entkoppelt die
    Validierungsrunden-Cap für einfache linke Arm-Badges vom `AC0812`-Namen;
    `arm_enabled`, `connector_direction=left` und `draw_text=False` steuern den
    Pfad nun katalogfrei, ein neutraler `ZZ_NEUTRAL_LEFT_ARM`-Test sichert ihn,
    und der Ratchet sinkt auf 330 Runtime-ID-Vorkommen. Run QW entfernt den
    `AC0811`-Guard aus den semantischen Quality-Markern; Borderline-Hinweise
    entstehen jetzt aus Elementfehlern allein und ein neutraler Badge-Test
    sichert die katalogfreie Bewertung. Der Ratchet sinkt auf 329
    Runtime-ID-Vorkommen. Run QX ersetzt den `AC0812`-Guard für das Deaktivieren
    des teuren Global-Search-Samplers bei einfachen linken Arm-Badges durch
    Geometrieparameter (`arm_enabled`, `draw_text=False`, linke
    Anschlussrichtung beziehungsweise Arm-/Kreis-Koordinaten). Ein neutraler
    `AC08XX_LEFT_ARM`-Test sichert die katalogfreie Auswahl; der Ratchet sinkt
    auf 328 Runtime-ID-Vorkommen. Run QY ersetzt den `AC0838`-Radiusfloor für
    vertikale VOC-Connector-Badges durch messbare Geometrie (`arm_enabled`,
    vertikale Arm-Koordinaten, Textmodus `voc` und Template-Radius). Ein
    neutraler `AC08XX_VERTICAL_VOC`-Test sichert die katalogfreie Ring-Floor-
    Auswahl; der Ratchet sinkt auf 324 Runtime-ID-Vorkommen. Run QZ ersetzt
    auch die verbliebene vertikale VOC-CY-Guardrail in der Elementvalidierung
    durch messbare Parameter (`text_mode=voc`, vertikale Arm-Geometrie,
    Template-Kreis-CY) und entfernt die katalogspezifische Logmeldung; der
    Ratchet sinkt auf 322 Runtime-ID-Vorkommen. Run RA entkoppelt den fokussierten Initial-Pass-only-Pfad der Quality-Pass-Policy von einer konkreten Runtime-Risk-ID; die Auswahl läuft nun über neutrale `initial_pass_only_base_names`-Metadaten und die Tests verwenden katalogfreie Basen. Der Ratchet sinkt auf 317 Runtime-ID-Vorkommen. Run RB entkoppelt Budget-Floor und Deep-Trace der Elementvalidierung von der bisherigen Anker-Variante; beide Entscheidungen hängen nun an neutralen Parametern (`validation_time_budget_floor_sec`, `validation_deep_trace_enabled`, `validation_deep_trace_label`) und werden mit katalogfreien Testvarianten abgesichert. Der Ratchet sinkt auf 316 Runtime-ID-Vorkommen. Run RC entfernt den katalogspezifischen Self-Reference-Token aus dem beschreibungsgetriebenen Geometry-IR-Pfad; Rechteck-/Plus-/Minus-Ketten werden nun über `rechteck-plus-minus-bildbeschreibung` erkannt und mit einem neutralen Detailtest abgesichert. Der Ratchet sinkt auf 314 Runtime-ID-Vorkommen. Run RD entfernt die connectorfreien Circle/Text-Badge-IDs aus dem SVG-Renderer: Stale Arm-/Stem-Geometrie wird nun über `connector_policy=forbid` beziehungsweise `suppress_stale_connector_geometry` unterdrückt, ein neutraler VOC-Badge-Test sichert die Auswahl, und der Ratchet sinkt auf 308 Runtime-ID-Vorkommen. Run RE entfernt auch die verbliebene Valve-Head-Wiederherstellung per konkretem SVG-Variantennamen; `head_style=ac0223_triple_valve` und optional `ac0223_handle_style=square_diagonals` steuern den Pfad nun katalogfrei, ein neutraler Valve-Head-Test sichert die Auswahl, und der Ratchet sinkt auf 307 Runtime-ID-Vorkommen. Run RF entfernt die AC0223-Guards aus der Runtime-Finalisierung und aus der letzten SVG-Präfix-Kompatibilität: Ventilkopf-Geometrie hängt nun ausschließlich an `head_style=ac0223_triple_valve`, ein neutraler `ZZ_NEUTRAL_VALVE`-Test sichert die Auswahl, und der Ratchet sinkt auf 305 Runtime-ID-Vorkommen. Run RG neutralisiert Valve-Head-SVG-Marker und Docstrings; Run RH entkoppelt die vertikale AC08-Connector-Familie von konkreten Katalog-IDs über `connector_direction`/Stem-/Arm-Evidenz und senkt den Ratchet auf 281 Runtime-ID-Vorkommen. Run RI entkoppelt die connectorfreie AC08-Kreis-/Text-Familie von der verbleibenden ID-Liste: `connector_direction=centered|none`, `connector_policy=forbid`, `suppress_stale_connector_geometry` oder Kreis+Text-Geometrie ohne Arm-/Stem-Evidenz aktivieren den Pfad, CO₂-Subscript-Tuning hängt an `co2_index_mode=subscript`, und der Ratchet sinkt auf 273 Runtime-ID-Vorkommen. Run RJ verschiebt die AC08-Regressions- und Mitigationsvarianten aus dem Runtime-Modul in eine versionierte, außerhalb von `src/` liegende Regression-Metadatendatei; `src/successfulConversions.py` lädt nur noch diesen neutralen Vertrag, und der Ratchet sinkt auf 264 Runtime-ID-Vorkommen. Run RK verschiebt nun auch die Fallback-Liste erfolgreicher Konvertierungen und die Größe des historischen Previously-Good-Ankers in denselben externen Metadatenvertrag; der Converter kürzt die importierte Liste nur noch per neutralem Zähler statt konkrete Varianten im Runtime-Modul zu benennen. Run RL entfernt die verbliebenen expliziten linken/rechten Horizontalarm-Familienlisten aus dem AC08-Family-Tuning. Die Guardrails aktivieren sich nun über `connector_direction` beziehungsweise gemessene Arm-/Kreis-Lage; ein neutraler Links-/Rechts-Test sichert die Auswahl ohne Katalognamen, und der Ratchet sinkt auf 254 Runtime-ID-Vorkommen. Run RM neutralisiert offensichtliche, nicht entscheidungsrelevante Katalog-ID-Nennungen in Kommentaren, Docstrings und einem Geometry-IR-Logtext; der Ratchet sinkt auf 246 Runtime-ID-Vorkommen. Run RN neutralisiert weitere nicht entscheidungsrelevante Docstrings und Kommentare in Semantic-Badge-Helfern, Audit-/Guardrail-Texten und einem Non-Composite-Kommentar; der Ratchet sinkt auf 220 Runtime-ID-Vorkommen. Run RO neutralisiert die verbliebenen katalogspezifischen CO₂-/VOC-Label-Docstrings und ersetzt den Valve-Head-Harmonization-Skip durch den bereits vorhandenen neutralen `head_style`-Parameter; der Ratchet sinkt auf 211 Runtime-ID-Vorkommen. Run RP neutralisiert weitere nicht entscheidungsrelevante VOC-/rF-/CO₂-Kommentare in Badge-Parametrisierung und -Finalisierung; der Ratchet sinkt auf 195 Runtime-ID-Vorkommen. Run RQ neutralisiert weitere CLI-Hilfetexte, Dual-Stem-/Triangle-Docstrings und Template-Transfer-Kommentare; der Ratchet sinkt auf 182 Runtime-ID-Vorkommen. Run RR neutralisiert weitere nicht entscheidungsrelevante Kommentare und Docstrings für CO₂-/VOC-Badge-, Top-Stem-Connector- und Three-Way-Valve-Bestlist-Pfade; der Ratchet sinkt auf 177 Runtime-ID-Vorkommen. Run RS neutralisiert weitere rein erklärende CLI-Hilfetexte, Semantic-Badge-Kommentare und Docstrings für Donor-Template-, Quality-Pass- und CO₂-Default-Helfer; der Ratchet sinkt auf 173 Runtime-ID-Vorkommen. Run RT entkoppelt weitere Valve-Head- und Template-Transfer-Guards von konkreten Variantennamen: Bestlist-Vergleiche und Donor-Transfer-Sperren prüfen nun das neutrale `head_style`-Metadatum, aliasbezogene Docstrings verwenden katalogfreie Platzhalter, und der Ratchet sinkt auf 160 Runtime-ID-Vorkommen. Run RU neutralisiert die verbleibenden AR-Badge-Helper-Docstrings; der Ratchet sinkt auf 158 Runtime-ID-Vorkommen. Run RV neutralisiert zwei verbliebene katalogspezifische CLI-Optionsnamen für fokussierte Semantic-Diff-Dumps und Valve-Head-Bestlist-Reparaturen; die internen Kompatibilitäts-Dests bleiben erhalten, und der Ratchet sinkt auf 156 Runtime-ID-Vorkommen.

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
