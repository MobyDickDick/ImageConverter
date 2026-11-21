# AC0152_L: SVG-Bauteile wieder konvertierbar

Nachtrag: Die spätere [Ebenen- und Überlappungskorrektur](../ac0152_layers_2026-11-21/README.md)
weist den hier noch akzeptierten übermalenden Griff mit einer lokalen Prüfung
zurück und korrigiert die Zeichenreihenfolge. Dieser Bericht beschreibt den
vorherigen Prüfstand.

Die unveränderte Bauteilliste lautet:

```text
SVG-Bauteil: AC0151_L.svg
SVG-Bauteil: AC1002_L.svg
```

## Ursachen und Korrektur

1. `AC1002_L.svg` enthielt eine zu dunkle Kreisfüllung und ein nach rechts
   verschobenes, schlecht erkennbares M. Der unveränderte Glyphenpfad ist jetzt
   mittig platziert; Kreis, Griff, Farben und Glyphenabmessungen wurden am
   Original `AC1002_L.jpg` vermessen. Es bleiben eine Gerade, ein Kreis und
   ein Glyphenpfad. Das Bauteil selbst besteht seine Rasterprüfung
   (IoU 0.8761, Kantenübereinstimmung 0.9004).
2. Die Platzierung begrenzte die vollständige Quellzeichenfläche. Deren leerer
   rechter Rand passt bei der benötigten Motorgrösse nicht ins Zielbild.
   Stattdessen wurde ein winziges Bauteil am unteren Röhrenrand gewählt.
   Jetzt werden die bereits gezeichneten, vom Quellviewport begrenzten Flächen
   mit Alpha und einem SVG-Renderer vermessen. Auch weisse Farbe und Konturen
   zählen. Nur transparente Ränder dürfen überstehen. Die Suche verwendet
   entsprechend beschnittene, proportional gerenderte Vorlagen und erlaubt
   bei Bedarf negative Positionen. Die gespeicherten Vektoren bleiben vollständig.
3. Die unabhängige Vorlagensuche verfehlte die Kantenprüfung noch knapp.
   Eine anschliessende begrenzte Suche prüft Position und proportionale Skalierung
   im tatsächlichen Gesamtbild. Hier genügt eine Verschiebung des Motors um
   einen halben Pixel nach unten. Explizite Positionen bleiben fest.

Es gibt keine Bild-ID-Sonderfälle im Produktionscode, keine veränderten
Qualitätsgrenzen und keine zusätzliche Rasterrekonstruktion. Die Röhre und die
gespeicherte Beschreibung bleiben unverändert. Die alte Motorquelle liegt in
`AC1002_L_before.svg` sowie in der regulären Projekt-SVG-Historie; auch das
vorherige Projektresultat wurde durch die reguläre GUI-Ablage archiviert.

## Ergebnis

Der echte GUI-Worker lief mit Profil `quick`, Seed 42 und ausgeschalteter
Wiederverwendung des aktuellen SVG. Nach 131 Renderprüfungen und etwa 22 Sekunden
meldet er **bestanden**. Die Ausgabe wurde automatisch als
`artifacts/converted_images/converted_svgs/AC0152_L.svg` gespeichert.

| Prüfung | Vorher | Korrigiertes gespeichertes SVG |
| --- | ---: | ---: |
| Normalisierter Pixelfehler | 0.0072364 | 0.0009215 |
| Vordergrund-IoU | 0.9343 | 0.9864 |
| Kantenübereinstimmung | 0.4918 | 0.7261 |
| Ergebnis | ungenügend | bestanden |

Alle gemalten Bauteilflächen liegen innerhalb der ursprünglichen 190 × 400 Pixel.
Bauteilinhalt, Verlauf und Konturen werden bei der abschliessenden Inventarprüfung
mit den aktuellen Quelldateien verglichen. Das ist eine bestandene Annäherung,
keine pixelidentische Kopie: Beispielsweise überlagert der unverändert kopierte
Motorgriff gemäss vorgegebener Zeichenreihenfolge einen kleinen Teil der Röhre.
Die allgemeine automatische Bauteilauswahl bleibt ausserhalb dieses Pakets.

## Prüfung und Reproduktion

```powershell
.venv/Scripts/python.exe -m pytest tests/test_svg_components.py tests/test_canvas_containment.py tests/test_description_language.py -q
```

**101 Tests bestanden.** Darunter sind der echte GUI-Worker mit dem gemeldeten
JPEG, erneute Prüfung der gespeicherten Ausgabe, unveränderte Quelldateien
während der Zusammensetzung, negative Positionen bei transparenten Rändern,
Ablehnung überstehender Konturen und Erfassung weisser Flächen. `git diff --check`
besteht für alle in diesem Paket bearbeiteten Produktions-, Test-, Dokumentations-
und SVG-Dateien. Ein späterer Gesamtlauf meldete zusätzlich CRLF-Zeilen in der
parallel bearbeiteten, hier unveränderten `AC0201_M.svg`.

`run_gui.py` wiederholt den vollständigen GUI-Worker samt regulärer Projektablage
(mit `PYTHONPATH=.` aus dem Projektverzeichnis). `repair_donor.py` dokumentiert die
Vermessung der Motorquelle und schreibt nur die separate korrigierte Vorlage.
`verify_composition.py` prüft die Zusammensetzung mit der isolierten Bibliothek.

Kompakte Messdaten: `donor_quality.json`, `gui_summary.json`, `saved_quality.json`.
Das separat aus dem gespeicherten Projekt-SVG gerenderte Ergebnis ist `final.png`.
Die Serveroberfläche muss nach einem Codeupdate neu gestartet werden, falls sie
noch alte Module geladen hat; laufende andere Aufträge vorher abschliessen.
