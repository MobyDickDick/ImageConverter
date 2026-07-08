# Nächstes Arbeitspaket – AC0840_L rF-Kreisbadge Textregistrierung Plan-B Run VX (2026-07-08)

Dieses Arbeitspaket formalisiert die angefragte Plan-B-Aufgabe für `AC0840_L`:
ein 28×28-Kreisbadge mit hellgrauer Füllung, grauer Kontur und zentralem
`rF`-Text. Der aktuelle Konvertierungsfehler ist textbezogen: Die Buchstaben
werden zu klein gerendert und liegen nicht passgenau über der Vorlage, sondern
sind sichtbar versetzt. Ziel ist ausdrücklich keine ID-spezifische Kopie der
gegebenen SVG, sondern ein allgemeiner, wiederverwendbarer Registrierungs- und
Skalierungspfad für kleine AC08-Textbadges.

## 1) Referenzbeschreibung / Eingabe

Die vom Nutzer gelieferte Referenz-SVG beschreibt folgende Semantik:

- Canvas `28×28`, `viewBox="0 0 28 28"`.
- Kreis-Hintergrund: Mittelpunkt `(14, 14)`, Radius `13.5`, Füllung `#f2f2f2`,
  Kontur `#7f7f7f`, Konturstärke `1`.
- Textinhalt `rF` in grauer Farbe `#7f7f7f`, Font-Familie
  `Arial, Helvetica, sans-serif`, Font-Grösse ca. `20.64px`, Font-Gewicht `600`.
- Textankerung ist mittig; die effektive Textlage nutzt zusätzlich eine leichte
  nicht-uniforme Skalierung (`scale(0.99645631,1.0035563)`) und liegt dadurch
  optisch auf der Kreisbadge-Mitte.

## 2) Fehlerbild

Die bisherige Konvertierung ist nicht zufriedenstellend, weil:

1. **Glyph-Skalierung zu klein:** Der `rF`-Text nutzt nicht genug Badge-Höhe und
   -Breite; die Zeichen wirken im Vergleich zur Vorlage geschrumpft.
2. **Textregistrierung versetzt:** Die Textmitte ist nicht deckungsgleich mit
   der Vorlage. Besonders bei kleinem 28×28-Raster führt schon ein Subpixel- oder
   Baseline-Fehler zu sichtbarem Offset.
3. **Baseline-/Anchor-Abgleich fehlt:** `dominant-baseline`, Font-Metriken und
   Renderer-spezifische Textboxen werden nicht robust genug in eine optische
   Glyph-BBox übersetzt.

## 3) Generische Plan-B-Aufgabe

Der Algorithmus soll einen generischen `CircleTextBadge`-/`RfTextBadge`-Pfad
ableiten, der kleine Kreisbadges mit kurzem Text über messbare Badge- und
Glyph-Parameter registriert:

1. **Badge-Erkennung:** Kreis oder nahezu kreisförmige helle Fläche erkennen und
   als `CircleBackground` mit `cx`, `cy`, `r`, `fill`, `stroke` und
   `stroke_width` parametrisieren.
2. **Text-Erkennung / Beschreibungskopplung:** Kurze Badge-Texte wie `rF` aus
   Beschreibung, OCR/Perception oder vorhandenen Text-Glyph-Kandidaten in eine
   `TextGlyph`-IR übernehmen. Die ID `AC0840_L` darf nur Testfixture sein.
3. **Optische Glyph-BBox:** Für die Textregistrierung nicht allein die SVG-
   Baseline verwenden, sondern eine gemessene oder approximierte optische
   Glyph-BBox. Parameter: `font_size`, `font_weight`, `anchor_x`, `anchor_y`,
   `baseline_adjust`, `scale_x`, `scale_y`.
4. **Skalierungsfit:** Font-Grösse so wählen, dass die optische `rF`-BBox einen
   festen Anteil der Kreisinnenfläche belegt, statt über generische kleine
   Default-Fontgrössen zu laufen.
5. **Subpixel-Registrierung:** Kleine lokale Probes für `anchor_x`, `anchor_y`,
   `baseline_adjust`, `scale_x` und `scale_y` erlauben, damit 28×28-Icons
   pixelnäher ausgerichtet werden können.

## 4) Akzeptanzkriterien

- `AC0840_L.jpg` wird ohne Runtime-Bild-ID-Abfrage über einen generischen
  Kreisbadge-Textpfad oder eine bestehende AC08-rF-Badge-Familie konvertiert.
- Die erzeugte SVG enthält semantische Vektorprimitive: einen Kreis-Hintergrund
  und ein echtes Text-/Glyph-Element, keine eingebetteten Rasterdaten.
- Der `rF`-Text ist grösser als im fehlerhaften Ausgangslauf und optisch auf die
  Referenzmitte registriert; die Buchstaben dürfen nicht mehr sichtbar nach
  links/rechts/oben/unten versetzt sein.
- Ein Regressionstest prüft mindestens eine synthetische 28×28-Variante mit
  ähnlichem Kreisbadge und kurzem Text, damit der Fix nicht nur für `AC0840_L`
  gilt.
- `tools/check_no_new_image_id_hardcoding.py` bleibt grün; `AC0840_L` darf nur
  in Tests, Dokumentation oder Fixture-/Artefaktpfaden erwähnt werden.

## 5) Vorgeschlagene Tests

- Unit-Test für `CircleTextBadge`-Parameter: 28×28-Kreisbadge mit `rF` erzeugt
  `font_size` im Bereich der Referenzgrösse und mittige Anchor-Parameter.
- Renderer-Test: Die SVG-Ausgabe enthält `circle` plus `text`/Glyph, nutzt graue
  Füllfarbe/Kontur und rendert ohne Rastereinbettung.
- Optimierer-Test: Lokale Probes dürfen `font_size`, `anchor_y` und
  `baseline_adjust` verändern und müssen eine kleinere Text-BBox-Abweichung
  gegenüber der Ausgangsvariante erreichen.
- Hardcoding-Test: Keine neue Runtime-Verzweigung auf `AC0840_L` oder feste
  AC0840-Dateinamen.

## 6) Perception-Lerneffekt

Der Lerneffekt ist `generalisiert`, wenn die Lösung als Kombination aus
`CircleBackground` und parametrischer `TextGlyph`-Registrierung funktioniert und
die optische Glyph-BBox für weitere kleine AC08-Textbadges wiederverwendbar ist.
Er wäre `nur Sonderfall`, wenn die exakten SVG-Koordinaten, der exakte
Transform-String oder eine explizite `AC0840_L`-Runtime-Verzweigung übernommen
würden.

## 7) Nächster sinnvoller Schritt

Die Plan-B-Aufgabe in der nächsten Umsetzungssession als isolierten
Textregistrierungs-Refresh ausführen: zuerst den bestehenden AC08-rF-Badge-Pfad
und vorhandene `TextGlyph`-/Kreisbadge-Tests identifizieren, danach Fontgrössen-
und Anchor-Probes parametrisch ergänzen und mit einem `AC0840_L`-Einzellauf plus
Hardcoding-Check absichern.
