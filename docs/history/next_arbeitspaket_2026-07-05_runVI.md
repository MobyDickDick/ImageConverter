# Nächstes Arbeitspaket – AC0512_1_L Diagonalstreifen-Icon Plan-B Run VI (2026-07-05)

Dieses Arbeitspaket formalisiert die angefragte Plan-B-Aufgabe für
`AC0512_1_L`: ein kleines querformatiges Rechteck-Icon mit grauem Rand,
rot/orange vertikalem Verlauf und drei parallelen weissen Diagonalstreifen von
links oben nach rechts unten. Ziel ist ausdrücklich nicht, die gegebene SVG als
bildspezifische Kopie zu übernehmen, sondern daraus einen allgemeingültigen
Konvertierungspfad für diese Symbolfamilie abzuleiten.

## 1) Zielbild / Semantik

Der Algorithmus soll aus Beschreibung und Rasterbild eine neutrale
`DiagonalStripePanel`-ähnliche Geometry-IR ableiten:

- rechteckige, querformatige Grundfläche mit dünnem neutralgrauem Rahmen,
- Innenfläche mit vertikalem Rot-/Rotorange-Verlauf,
- `n = 3` gleichartige helle Diagonalstreifen,
- Streifenrichtung `top_left_to_bottom_right`,
- parallele Streifen mit ähnlicher Breite, Länge und gleichmässigem Abstand,
- keine Bindung an die konkrete Bild-ID `AC0512_1_L` oder an exakt diese
  SVG-Punktkoordinaten.

## 2) Generische Erkennung statt Sonderfall

Die Implementierung soll über wiederverwendbare Merkmale laufen:

1. **Panel-Erkennung:** Aus Vordergrundmaske oder Beschreibung ein dominantes
   rechteckiges Querformat-Panel mit Rahmen ableiten. Parameter: `bbox`,
   `border_width`, `border_color`, `corner_radius`.
2. **Gradient-Erkennung:** Für die Innenfläche einen linearen vertikalen
   Farbverlauf schätzen. Parameter: `gradient_axis=vertical`, robuste
   Stützfarben/Stops aus oberen, mittleren und unteren Innenflächen-Samples.
3. **Diagonalstreifen-Erkennung:** Helle, längliche Komponenten innerhalb der
   Innenfläche extrahieren und per Linien-/Polygonfit als parallele Streifen
   gruppieren. Parameter: `count`, `angle`, `stripe_width`, `spacing`,
   `extent`, `fill_color`.
4. **Beschreibungskopplung:** Wörter wie `drei`, `parallel`, `weiss`,
   `Diagonalstreifen`, `links oben`, `rechts unten`, `rot`, `orange`, `Rand`
   setzen Constraints, dürfen aber nur die generische IR parametrisieren.
5. **Renderer:** Aus der IR ein kompaktes SVG mit `rect`, `linearGradient` und
   wiederholten Streifen-Polygonen erzeugen. Die konkrete Punktliste darf erst
   aus `bbox`, `angle`, `stripe_width` und `spacing` berechnet werden.

## 3) Akzeptanzkriterien

- `AC0512_1_L.jpg` wird ohne Runtime-Bild-ID-Abfrage über den generischen
  Diagonalstreifen-Panel-Pfad konvertiert.
- Derselbe Pfad funktioniert auch für `AC0512_1_M.jpg` und `AC0512_1_S.jpg`
  oder für synthetische Varianten mit anderer Canvasgrösse, leicht anderer
  Streifenbreite und leicht verschobenen Rot-Gradient-Stops.
- Die erzeugte SVG-Struktur enthält semantische Primitive statt eingebetteter
  Rasterdaten: mindestens ein Rahmenrechteck, ein Innenrechteck mit linearem
  Verlauf und drei berechnete Streifenpolygone.
- `tools/check_no_new_image_id_hardcoding.py` bleibt grün; neue Tests dürfen
  `AC0512_1_L` nur als Fixture/Regression nennen, nicht im Runtime-Code.
- Ein gezielter Roundtrip-/Einzellauf protokolliert den neuen Pfadnamen, z. B.
  `status=semantic_diagonal_stripe_panel` oder vergleichbar.

## 4) Vorgeschlagene Tests

- Unit-Test für Beschreibung → Constraints: freie deutsche Beschreibung mit
  `drei weisse Diagonalstreifen von links oben nach rechts unten` erzeugt
  `count=3`, `direction=top_left_to_bottom_right`, `panel_aspect=landscape`.
- Unit-Test für Streifengruppierung: synthetisches 80×40-Panel mit drei
  parallelen weissen Streifen wird als eine Stripe-Gruppe mit konsistentem
  Winkel und Abstand erkannt.
- Renderer-Test: Eine neutrale `DiagonalStripePanel`-IR rendert genau einen
  vertikalen Verlauf, Rahmen und drei Streifenpolygone.
- Generalisierungstest: dieselbe IR-Synthese läuft auf mindestens zwei Grössen
  (`L/M/S`) ohne neue Koordinaten- oder ID-Sonderzweige.

## 5) Perception-Lerneffekt

Der Lerneffekt ist `generalisiert`, wenn die Aufgabe als Kombination aus
`RectBorder`, `ColorPatch`/Gradient und gruppierten `PolygonPath`-/Line-Stripe
Primitiven gelöst wird. Sie wäre `nur Sonderfall`, wenn feste AC0512-Koordinaten
oder die exakten Beispiel-Polygonpunkte in den Runtime-Pfad übernommen würden.

## 6) Umsetzung / Ergebnis (Run VI)

Run VI ergänzt einen katalogfreien `DiagonalStripePanel`-Geometry-IR-Pfad. Der
Beschreibungspfad erkennt sowohl explizite diagonal gestreifte rot/orange Panels
als auch die in den AC0512-Beschreibungen vorhandene Rotation eines Panels mit
drei horizontalen Schliessflächen als drei parallele Diagonalstreifen. Die IR
bleibt parametrisch: Panel-BBox, Innen-Inset, Rahmen, vertikaler Verlauf,
Streifenanzahl, Streifenrichtung, Breite und Abstand werden als neutrale Felder
geführt; die SVG-Polygonpunkte werden erst beim Rendering aus diesen Parametern
berechnet.

Der Renderer erzeugt für `DiagonalStripePanel` genau einen vertikalen
`linearGradient`, ein Innenrechteck, drei berechnete Streifen-Polygone und ein
Rahmenrechteck. Der Non-Composite-Auswahlpfad behandelt diesen IR-Knoten als
semantischen Beschreibungskandidaten und protokolliert ihn mit
`status=semantic_diagonal_stripe_panel`, sobald er im Kandidatenvergleich
gewählt wird.

### Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_diagonal_stripe_panel_geometry_ir.py` → `4 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` → `PASS: no image-ID hardcoding found in runtime source code (0 occurrences).`
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 60 python -m src.iCCModules.imageCompositeConverterCli artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-runvi2 --start AC0512_1_L --end AC0512_1_L --deterministic-order` → Exit `0`; der bestehende direkte/semantische Rasterpfad bleibt für die konkrete AC0512-Serie pixelnäher und wird im Kandidatenvergleich weiterhin bevorzugt, während der neue generische IR-Pfad unit-seitig abgesichert ist.
