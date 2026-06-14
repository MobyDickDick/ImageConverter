# Zielarchitektur: Bild + Beschreibung → SVG

## Klare Bestandsaufnahme

Das Ziel ist möglich, aber der aktuelle Konverter erfüllt es noch nicht. In den Runtime-Modulen existieren zahlreiche katalog- und bildspezifische IDs sowie daraus abgeleitete Familienregeln. Diese Regeln sind trainiertes Wissen über konkrete Eingaben und gehören langfristig **nicht** in den Programmcode.

`config/legacy_image_id_baseline.json` ist ausschließlich ein Migrations-Ratchet: Der Konverter lädt diese Datei nie. Sie inventarisiert den heutigen technischen Schuldenstand, damit jede Anzahl nur sinken darf und keine neue Bild-ID unbemerkt in `src/` gelangt. Sie ist ausdrücklich keine Template- oder Bildwissensdatenbank.

## Gewünschter Datenfluss

1. **Eingabe:** Rasterbild plus freie Bildbeschreibung; Dateiname/ID dient nur der Zuordnung und dem Ausgabename.
2. **Wahrnehmung:** Generische Detektoren erzeugen Kandidaten für Konturen, Flächen, Kreise, Linien, Textbereiche, Symmetrien und Beziehungen.
3. **Beschreibung:** Ein Parser übersetzt Wörter wie „Kreis“, „links“, „senkrecht“, „CO₂“ oder „ohne Buchstabe“ in eine bildunabhängige Szenengraph-/Geometry-IR.
4. **Fusion:** Bildkandidaten und Beschreibungs-Constraints werden probabilistisch bzw. über gewichtete Kosten zusammengeführt. Die Beschreibung darf fehlende Details einschränken, aber keine Geometrie eines Katalogeintrags liefern.
5. **Rekonstruktion:** Primitive und Pfade werden aus Messwerten parametrisiert; keine Auswahl anhand einer Bild-ID.
6. **Optimierung:** Das gerenderte SVG wird gegen das Eingabebild optimiert. Semantische Constraints verhindern zwar optisch billige, aber inhaltlich falsche Lösungen.
7. **Unsicherheit:** Bei widersprüchlicher oder unzureichender Evidenz liefert der Konverter ein Diagnoseergebnis statt eines vermeintlich sicheren SVGs.

## Zulässige Konfiguration

Eine kleine JSON-Datei ist sinnvoll für **globale, bildunabhängige** Einstellungen, beispielsweise:

- unterstützte Primitive und Synonyme,
- Gewichte für Pixel-, Kanten-, Struktur- und Beschreibungskosten,
- allgemeine Größen-/Farb-/Komplexitätsgrenzen,
- Optimierungsbudget und Abbruchregeln,
- Schwellen für Unsicherheit und manuelle Prüfung.

Nicht zulässig sind Bild-IDs, Dateinamen, katalogspezifische Aliaslisten, gespeicherte Koordinaten konkreter Bilder, Referenz-SVG-Pfade oder Regeln wie „für ACxxxx verwende Familie Y“. Ein solches JSON würde das Hardcoding nur aus Python verlagern.

## Migrationsplan

Die daraus abgeleiteten, einzeln prüfbaren Arbeitspakete stehen in
`docs/image_description_only_tasks.md`.

### Phase 1 – weiteres Lernen am Testkatalog stoppen

- `tools/check_no_new_image_id_hardcoding.py` in CI ausführen.
- Neue Qualitätsverbesserungen nur über messbare Bildmerkmale oder Beschreibungssignale implementieren.
- Katalog-SVGs und Bild-IDs ausschließlich als Tests/Benchmarks behandeln.

### Phase 2 – ID-Dispatch durch Merkmals-Dispatch ersetzen

Für jede bestehende ID-Regel wird dokumentiert, welche beobachtbare Eigenschaft sie eigentlich repräsentiert (z. B. Kreis mit linkem Anschluss und Text). Danach wird die Regel durch einen generischen Feature-Prädikator ersetzt. Nach jedem Ersatz wird der entsprechende Baseline-Eintrag verkleinert; `--update` darf nur bei bewusstem Abbau oder nach Review verwendet werden.

### Phase 3 – einheitliche Geometry-IR

Alle Spezialrenderer werden auf wenige Primitive und Beziehungen zurückgeführt: Kreis/Ellipse, Linie, Polygon, Bézierpfad, Text/Glyph, Füllung/Kontur, Überdeckung, Anschluss, Ausrichtung und Symmetrie. Beschreibung und Bildanalyse müssen dieselbe IR erzeugen bzw. ergänzen.

### Phase 4 – Generalisierung beweisen

- Ein strikt zurückgehaltener Testsatz darf während der Entwicklung weder IDs noch erwartete SVG-Geometrien in Runtime-Code oder Konfiguration einbringen.
- Zusätzlich werden Dateinamen zufällig umbenannt. Identische Pixel + Beschreibung müssen (bis auf Metadaten/Ausgabename) dasselbe SVG ergeben.
- Ablationstests messen Bild allein, Beschreibung allein und Bild + Beschreibung.
- Akzeptanz erfolgt über Rasterähnlichkeit, Kanten-/Strukturmetriken, semantische Constraints, SVG-Komplexität und Unsicherheitskalibrierung.

## Realistische Qualitätsgrenze

Für technische Symbole, Icons, Logos und flächige Grafiken ist „genügend gute“ Rekonstruktion realistisch. Für beliebige Fotos ist eine semantisch gleichwertige, kompakte Vektorisierung grundsätzlich mehrdeutig; dort muss das Ziel entweder auf kontur-/posterartige Vektorisierung begrenzt oder ein lernendes Vektor-Generierungsmodell eingesetzt werden. Auch dann bleiben Bild und Beschreibung die einzigen eingabespezifischen Informationen.
