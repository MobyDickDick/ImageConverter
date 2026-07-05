# Nächstes Arbeitspaket – AC0832 CO²-Kelle mit linkem Griff Plan-B Run VJ (2026-07-05)

Dieses Arbeitspaket formalisiert die angefragte Plan-B-Aufgabe für die in den
Samples enthaltene `AC0832`-Familie: eine stilisierte Kelle mit kurzem
horizontalem Griff nach links und einer runden, hell gefüllten Scheibe rechts.
In der Scheibe steht `CO²`, wobei die `2` hochgestellt ist. Die vom Nutzer
mitgelieferte SVG dient nur als semantische Referenz; der Runtime-Pfad darf
keine exakten Beispielkoordinaten oder Bild-ID-Sonderlogik übernehmen.

## 1) Zielbild / Semantik

Der Algorithmus soll aus Beschreibung und Rasterbild eine neutrale
`LeftHandleCO2KelleBadge`-ähnliche Geometry-IR ableiten:

- runde Badge-/Kellenscheibe mit neutralgrauer Kontur und heller Füllung,
- kurzer, horizontaler Griff links, zentriert auf der Kreis-Symmetrieachse,
- Griff und Kreis berühren oder überlappen sich leicht, ohne sichtbare Lücke,
- Textlabel `CO²` in der Kreisscheibe,
- `2` als Superskript, nicht als Grundlinien-`CO2` und nicht als tiefgestelltes
  `CO₂`,
- horizontale Textausrichtung bleibt erhalten, auch wenn die Kellengeometrie als
  gedrehte Variante einer Grundform beschrieben wird,
- Größenparameter werden aus Canvas, Kreisradius, Grifflänge und Text-Bounds
  berechnet statt aus festen Pixelkoordinaten.

## 2) Generische Erkennung statt Sonderfall

Die Implementierung soll über wiederverwendbare Merkmale laufen:

1. **Kellen-/Badge-Erkennung:** Kreis-/Ringkandidat mit heller Innenfläche und
   neutralgrauer Kontur als `CircleBackground` oder äquivalentes Badge-Primitive
   erfassen. Parameter: `center`, `radius`, `fill_color`, `stroke_color`,
   `stroke_width`.
2. **Griff-Erkennung:** Eine horizontale, links vom Kreis liegende Linie oder
   ein schmales Rechteck als `HorizontalRule`/Connector bestimmen. Parameter:
   `x1`, `x2`, `y`, `width`, `cap_style`, relative Überlappung zum Kreis.
3. **Text-/Glyph-Erkennung:** `CO` und Superskript-`2` als zusammengehöriges
   Label modellieren. Parameter: `label=CO²`, `superscript=true`, Textfarbe,
   Fontgewicht, relative Textbox-Lage im Kreis.
4. **Beschreibungskopplung:** Wörter wie `Kelle`, `Löffel`, `Griff links`,
   `kreisrunde Scheibe`, `CO²`, `hochgestellt` und `Superskript` setzen
   Constraints, dürfen aber nur die generische IR parametrisieren.
5. **Renderer:** Aus der IR ein kompaktes SVG mit Kreis, Griff und separatem
   `CO`-/Superskript-Text erzeugen. Die Superskript-Position wird relativ zu
   Kreisradius und `CO`-Textbox berechnet.

## 3) Akzeptanzkriterien

- `AC0832_L.jpg`, `AC0832_M.jpg` und `AC0832_S.jpg` werden ohne
  Runtime-Bild-ID-Abfrage über denselben generischen linken Kellen-/CO²-Pfad
  konvertiert.
- Die erzeugte SVG-Struktur enthält semantische Primitive statt eingebetteter
  Rasterdaten: mindestens einen Kreis, einen horizontalen linken Griff und ein
  zweigeteiltes oder semantisch markiertes Superskript-Label `CO²`.
- `CO²` wird als hochgestellte `2` gerendert; Regressionen gegen
  AC0820-ähnliche tiefgestellte CO₂-Badges sind explizit ausgeschlossen.
- `tools/check_no_new_image_id_hardcoding.py` bleibt grün; neue Tests dürfen
  `AC0832_*` nur als Fixture/Regression nennen, nicht im Runtime-Code.
- Ein gezielter Roundtrip-/Einzellauf protokolliert den neuen Pfadnamen, z. B.
  `status=semantic_left_handle_co2_kelle_badge` oder vergleichbar.

## 4) Vorgeschlagene Tests

- Unit-Test für Beschreibung → Constraints: freie deutsche Beschreibung mit
  `Kelle`, `Griff links`, `kreisrunde Scheibe`, `CO²` und `hochgestellter 2`
  erzeugt `handle_direction=left`, `label=CO²`, `index_mode=superscript`.
- Unit-Test für Glyph-Modellierung: `CO²` wird in `CO` plus hochgestellte `2`
  zerlegt und nicht als tiefgestelltes `CO₂` oder normales `CO2` behandelt.
- Renderer-Test: Eine neutrale `LeftHandleCO2KelleBadge`-IR rendert genau einen
  Kreis, einen linken horizontalen Griff und das Superskript-Label innerhalb der
  Kreisscheibe.
- Generalisierungstest: dieselbe IR-Synthese läuft auf mindestens zwei Größen
  (`L/M/S`) und auf synthetischen Varianten mit leicht anderer Griff- und
  Kreisgröße ohne neue Koordinaten- oder ID-Sonderzweige.

## 5) Perception-Lerneffekt

Der Lerneffekt ist `generalisiert`, wenn die Aufgabe als Kombination aus
`CircleBackground`, `HorizontalRule`/Connector und `text_glyph` mit
Superskript-Index gelöst wird. Sie wäre `nur Sonderfall`, wenn feste
AC0832-Koordinaten, die exakten Beispiel-SVG-Transformationen oder eine
Runtime-Abfrage auf `AC0832` übernommen würden. Vor der Umsetzung soll zusätzlich
protokolliert werden, ob Kreis, Griff und Text bereits als Perception-Seeds vor
der ersten Optimierungsiteration erkannt werden.

## 6) Umsetzung / Ergebnis (Run VJ)

Run VJ ergänzt die freie Beschreibungskopplung für linke CO²-Kellen-Badges: Eine
neutrale Beschreibung mit `Kelle`, `Griff links`, `CO²` und `hochgestellter 2`
setzt nun katalogfrei dieselben semantischen Constraints wie der vorhandene
linke Circle-/Arm-Badge-Pfad (`semantic_badge`, Label `CO_2`, linker
Horizontal-Connector und `co2_index_mode=superscript`). Zusätzlich ist der
AC0832-Renderer strukturell abgesichert: Die generierte SVG enthält einen linken
horizontalen Griff, einen Kreis sowie getrennte `CO`- und hochgestellte `2`-
Textelemente statt eines Raster-Fallbacks.

Der gezielte AC0832-Einzellauf bestätigt weiterhin den semantischen Badge-Pfad
für `AC0832_L/M/S` (`mode=semantic_badge`, Elemente `circle,arm,text`). Die in
den vorhandenen XML-Beschreibungen enthaltene Aliasformulierung nennt nur die
Rotation und keinen expliziten CO²-Text; deshalb bleibt der konkrete Lauf beim
bisherigen Alias-Label `T`. Der neu ergänzte CO²-/Superscript-Zweig ist über
freie, katalogfreie Zielbeschreibungen abgesichert und vermeidet weiterhin neue
Runtime-Bild-ID-Abfragen.

### Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_semantic_family_rules_helpers.py::test_apply_semantic_badge_description_rules_derives_left_handle_co2_superscript_badge tests/test_image_composite_converter.py::test_generate_badge_svg_ac0832_has_left_handle_circle_and_superscript_label` → `2 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` → `PASS: no image-ID hardcoding found in runtime source code (0 occurrences).`
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0832-runVJ --start AC0832_L --end AC0832_S --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` → Exit `0`; der Lauf protokolliert für `AC0832_L/M/S` den semantischen Badge-Pfad mit `Elemente=circle,arm,text`.
