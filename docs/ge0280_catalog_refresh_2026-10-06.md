# GE0280 â€“ fÃ¤lschlicher Buchstabe in der Katalogausgabe

Die Vorlage und ihre originale XML-Beschreibung zeigen eine blaue Kugel
ohne Beschriftung. Das regulÃ¤re `converted_svgs/GE0280.svg` enthielt trotzdem
ein `B`. Das alte Validierungslog wÃ¤hlte
`non_composite_perception_seeded_geometry_ir` mit `CircleBackground` und
`TextGlyph` anhand des Pixel-Fehlers. Die Wahrnehmung hatte den Farbverlauf
fÃ¤lschlich als Glyph interpretiert.

Die neue katalogfreie Radialregistrierung aus dem GE0281-Arbeitspaket
erzeugte bereits die richtige Kreisstruktur. Die letzte Abnahme speicherte
diese SVGs jedoch nur im isolierten Evidenzordner; die regulÃ¤re Katalogausgabe
und deren Bestenlisten-Snapshot blieben auf dem alten Stand.

Ein frischer CLI-Lauf mit Originaldateiname `GE0280.jpg`, unverÃ¤nderter
Originalbeschreibung, Seed 0 und `semantic-only` erzeugt jetzt genau
denselben Kreis mit nativem Radialverlauf wie der zuvor umbenannte Holdout.
Das SVG enthÃ¤lt weder Text noch eingebettete Raster. Beide harten Gates
bestehen ohne Metrikregression. `mean_delta2` sinkt von `5049.623535`
auf `459.058960`.

Die regulÃ¤re SVG-Ausgabe, PNG-Vorschau, Differenzbilder, Validierungslogs
und der Bestenlisten-Snapshot einschlieÃŸlich Metadaten sind aktualisiert.
Der falsche Vorlauf bleibt ausschlieÃŸlich im Belegordner
`artifacts/evaluation/radial_disk_catalog_refresh_2026-10-06/before/`
als historische Diagnose erhalten.

Der Runtime-Regressionstest verwendet nun sowohl GE0280 als auch GE0281
mit ihren tatsÃ¤chlichen XML-Beschreibungen. Er verlangt identische SVGs
nach Umbenennung, die reine Kreisstruktur und keine Textelemente und
verbietet Sample-Zugriff sowie Raster-Embedding. Alle 34 fokussierten
Disk-Tests bestehen. SyntaxprÃ¼fung, CLI-Help-Smoke und Runtime-ID-NullprÃ¼fung
sind grÃ¼n. Der Gesamtlauf wird in `completion.json` im Belegordner dokumentiert.
