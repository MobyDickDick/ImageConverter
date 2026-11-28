# AP 2 – Flexible geometrische Repräsentation

Stand: 28. November 2026. Grundlage: AP 0, Abschnitt 8.
Ausgangscommit: `d996f093a0e3c56f59e03e6f6588fd9da99efac9`.
Entwicklung ausschliesslich auf `experimental/explorative-conversion`.

## Umfang und Schnittstelle

AP 2 liefert eine beschreibungsunabhängige Repräsentation und die Operationen,
mit denen eine spätere Suche ihre Objektstruktur ändern kann. Die sechs Typen
`circle`, `ellipse`, `rect`, `square`, `triangle` und `line` sind ohne feste
Objektzahl frei kombinierbar. Eine Beschreibung wird hier weder benötigt noch
interpretiert. Unbekannte Satzmuster können diesen Einstieg daher nicht blockieren.

```python
from src.exploratory import Candidate, Paint, Primitive, Relation, Scene, convert

scene = Scene(width=200, height=100).add(
    Primitive("body", "ellipse", center=(.4, .5), size=(.3, .6),
              paint=Paint(fill=(200, 30, 40))))
expanded = scene.add(
    Primitive("edge", "line", center=(.7, .5), size=(.3, .1),
              paint=Paint(fill=None, stroke=(20, 20, 20), stroke_width=.02)))
retyped = expanded.update("body", kind="rect")
reordered = retyped.reorder(("edge", "body"))
related = reordered.with_relations((
    Relation("contact", ("body", "edge"), anchors=("right", "start")),))
errors = related.relation_errors()
smaller = related.remove("edge")

# image ist ein BGR-uint8-Raster mit 200 x 100 Pixeln.
def source(image, description):
    yield Candidate.from_scene(scene, "initial")
    yield Candidate.from_scene(related, "structure_edit")

# result = convert(image, description="", sources=[source], seconds=300)
# result.best.scene enthält weiterhin die strukturierte Szene des Entwurfs.
```

## Datenvertrag

- `Scene`, `Primitive`, `Paint` und `Relation` sind unveränderliche Werte.
  Listen aus Aufrufern werden in Tupel überführt; Änderungen liefern neue Szenen.
  Beste Entwürfe werden damit durch spätere Strukturänderungen nicht überschrieben.
- Objekt-IDs sind eindeutig und bleiben bei Parameter- und Typänderungen stabil.
  Entfernen eines Objekts entfernt seine Beziehungen; andere IDs bleiben erhalten.
  Ein Typwechsel mit unpassenden Ankern wird ausdrücklich abgelehnt. Die Suche
  kann zuerst Beziehungen ändern und anschliessend den Typ wechseln.
- Objektfolge ist Zeichenreihenfolge. `reorder` erlaubt Änderungen der Überdeckung.
  Leere Szenen sind zulässige Zwischenzustände. Ohne Hintergrund und Objekte
  entsteht kein gültiger AP-1-Kandidat; dessen bestehende Prüfung lehnt ihn ab.
- Mittelpunkt und Ausdehnung sind Anteile von Breite/Höhe; Winkel sind Umdrehungen
  modulo 1. Strichbreite ist ein Anteil der kleineren Bilddimension. Farben sind
  RGB-Ganzzahltripel, der Rastereingang des Konverters bleibt BGR.
- Positionen dürfen ausserhalb der Zeichenfläche liegen; Grössen müssen endlich
  und positiv sein. Es gibt keine versteckte Beschneidung oder Grössenreparatur.
  Kreis und Quadrat verwenden die kleinere der beiden Ausdehnungen in Pixeln.
  Bei Linien bestimmt die erste Ausdehnung die Länge. Dreiecke sind wie im
  wiederverwendeten Bestand gleichschenklig; der Winkel zeigt zur Spitze.
- `Paint` unterstützt Vollfarbe, keine Füllung, optionale Kontur und Strichbreite
  einschliesslich null. Linien brauchen eine sichtbare Kontur. Gradienten, Text
  und beliebige Polygone gehören nicht zum Umfang dieses Arbeitspakets.
- `to_dict`/`from_dict` ermöglichen einen JSON-Rundlauf für Diagnose und spätere
  Checkpoints. Es wird keine Datei automatisch geladen oder geschrieben.

## Beziehungen und Wiederverwendung

`mirror`, `parallel`, `contact` und `coincident` sind eigenständige geometrische
Hypothesen. `relation_errors()` liefert pro Beziehung einen dimensionslosen,
nichtnegativen Fehler. Spiegelung vergleicht Typ, Mittelpunkt, effektive Grösse
und Orientierung an einer horizontalen oder vertikalen Achse. Parallelität
vergleicht lokale Richtungsachsen modulo 180 Grad. Kontakt und gemeinsame Anker
vergleichen die ausdrücklich benannten Punkte.

Anker: Mittelpunkt; lokale Seitenmitten bei Kreis, Ellipse und Rechteck/Quadrat;
Start/Ende bei Linien; Spitze und Basisenden bei Dreiecken; Ecken bei Rechtecken
und Quadraten. Kontakt ist damit eine Ankerbeziehung, keine allgemeine
Konturberührungs- oder Kollisionsprüfung. Konturstärke und Verdeckung fliessen
nicht in diese geometrischen Fehler ein. Beziehungen reparieren die Szene nicht
automatisch, beeinflussen in AP 2 noch nicht den Konverterscore und behaupten
keine Erfüllung sprachlicher Anforderungen. `released` bleibt unverändert falsch.

`adapters.scene_geometry` verwendet `geometry` und `STRIDE` aus dem vorhandenen
`imageCompositeConverterSceneProgram`. Die vorhandenen Formeln für Platzierung,
Rotation, Eckpunkte, Linienenden und Dreiecke werden wiederverwendet. Der strikte
Beschreibungsparser, sein Inventarlimit und Suchkonfigurationen werden nicht
aufgerufen. Legacy-Kontur-/Farbmetadaten werden durch die tatsächlichen Szenenwerte
ersetzt. Der kleine SVG-Export schreibt ausschliesslich native Grundformen mit
Vollfarben und benötigt keine Änderung der bestehenden SVG-Zulassungsprüfung.
Rendering und Vollbildmetriken laufen weiterhin über die AP-1-Adapter.

`Candidate.from_scene` verbindet die Szene mit dem vorhandenen Suchkern.
`best.scene` und `best.svg` bewahren auch unzureichende echte Vektorentwürfe.
Szenen mit einer vom Referenzraster abweichenden Zeichenfläche werden vor dem
Rendering zurückgewiesen. Bestehende reine SVG-Anbieter bleiben kompatibel.
Die AP-1-Startanbieter und ihre Auswahl werden nicht verändert.

## Abnahme und nächste Schritte

Tests ausschliesslich in GitHub Actions: Workflow `Exploratory acceptance`,
Windows/Linux, Python 3.10.11, AP 1 und AP 2 gemeinsam. Die Abnahme umfasst
variable Inventare über dem Legacy-Limit, leere Zwischenzustände, unabhängige
Strukturänderungen, JSON-Rundlauf, ungültige Referenzen/Parameter, alle sechs
Grundformen auf rechteckiger Zeichenfläche, Beziehungsfehler, echten Rasterexport,
sichtbare Ebenenwechsel, konkurrierende strukturelle Kandidaten und Entwurfserhalt
bei ungenügender Qualität. JUnit-Berichte werden als CI-Artefakte gespeichert.
Der konkrete CI-Status wird im Pull Request nachgewiesen; kein lokaler Testlauf.

AP 2 ist die Grundlage für Struktursuche, noch keine automatische Suche über
Objektzahlen. AP 3 erzeugt rasterbasierte Hypothesen; AP 4 kombiniert Pool,
Strukturmutationen und Parameteroptimierung unter einem gemeinsamen Budget.
Das Budget von beispielsweise 300 Sekunden wird in AP 2 nicht durch künstliche
Wartezeit ausgeschöpft. AP 5 behandelt Sprachhinweise und explizite Anforderungen;
AP 6–8 ergänzen persistente Ausgabe, Generalisierung und Integration.
Keine bildspezifische Sonderlösung und keine Änderung an Legacy-Dateien.

Die abgestimmten nächsten Etappen, ihre Abnahmekriterien und die Grenzen für
Aufwand und CI-Bereinigung stehen im
[weiteren Vorgehen nach AP 2](Weiteres_Vorgehen_nach_AP2.md).
