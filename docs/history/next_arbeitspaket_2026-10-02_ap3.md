# Nächstes Arbeitspaket – AP3 Qualitätswarteschlange (2026-10-02)

Dieses Paket setzt **AP3** aus
`next_arbeitspakete_aus_artifacts_2026-10-01.md` als reproduzierbaren,
laufgebundenen Auswahlprozess um. `tools/build_quality_queue.py` akzeptiert
ausschließlich einen vom AP4-Gate als `complete` bestätigten Reportstand. Der
partielle Repository-Snapshot kann deshalb weiterhin ausdrücklich keine neue
Qualitätswarteschlange erzeugen; die CLI endet dort ungleich null.

## Auswahlvertrag

- Die Result-Map, der Checkpoint und das Abschlussmanifest müssen dieselbe
  Run-ID und dieselben Abschlusszähler besitzen.
- Semantische Fehler und `needs_review`-Resultate werden nicht als
  Pixeloptimierungsfälle einsortiert.
- Technisch erfolgreiche Resultate werden nach `mean_delta2` absteigend
  sortiert. Höchstens zwei Kandidaten derselben zweistelligen Katalogfamilie
  werden aufgenommen, damit die maximal fünf aktiven Plätze nicht von einer
  einzelnen Familie belegt werden.
- Jeder Eintrag dokumentiert zusätzlich `spatial_quality_score`, Bildfläche,
  strukturierte Fehlerverteilung, Erzeugungspfad, erwartete Vorher-/SVG-/Diff-
  Artefakte und eine aus der Fehlerverteilung abgeleitete Restfehlerhypothese.
- `--limit` erlaubt ein bis fünf aktive Kandidaten; mehr als fünf akzeptiert
  die CLI nicht.

## Operative Verwendung

Nach Abschluss des externen AP0-Laufs wird die Warteschlange mit dessen
Reportverzeichnis erzeugt:

```bash
python tools/build_quality_queue.py /pfad/zum/reports \
  --input-dir /pfad/zu/den/eingabebildern \
  --output /pfad/zum/reports/conversion_quality_queue.json
```

Damit stammt die Auswahl ausschließlich aus der abgeschlossenen Vollmenge.
Der eingecheckte partielle Snapshot bleibt unverändert und wird nicht als
vermeintlich aktuelle Bestenliste ausgegeben. Fixture-Tests sichern die
Complete-Voraussetzung, den Ausschluss semantischer Fehler, die Familienbreite
und die Obergrenze der aktiven Kandidaten ab.
