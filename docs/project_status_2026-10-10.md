# Projektstand am 2026-10-10

Der Konverter ist batchfähig, aber noch kein verlässlich universeller
Bildkonverter. Für unterstützte Formkombinationen verarbeitet die Software
Bild und Beschreibung selbstständig. Eine Konvertierung benötigt weder einen
Chat noch eine von Codex erzeugte SVG-Vorlage. Bei noch nicht unterstützten
Motiven oder unzutreffenden Beschreibungen ist weiterhin Entwicklungsarbeit
erforderlich. Der bisherige Fortschritt erschließt hauptsächlich einzelne
Topologien mit Farb-, Größen- und Geometrievarianten.

## Was geprüft wurde

- Standard-Einstieg: `python -m src.imageCompositeConverter`, Ordner als Eingabe,
  `semantic-only` als voreingestellter Ausführungsmodus.
- Runtime: Beschreibungsspezifische, rastergestützte Registrierungen für
  begrenzte Topologien. Sie bestimmen Parameter aus Pixeln; neue Motive werden
  dadurch noch nicht automatisch aus beliebigen Primitiven zusammengesetzt.
- Runtime-ID-Nullprüfung: keine Bild-/Katalog-ID-Vorkommen in `src/`.
- Kataloginventar: **1.785 unterschiedliche JPG-Dateinamen** unter
  `artifacts/images_to_convert/`, rekursiv, ohne `samples`.
- XML: **707 Einträge**, davon **237** mit einem der Hinweise
  `platzhalter`, `unzugeordnete wurzelform`, `manuell prüfen` oder
  `manuell zu prüfen`. **178** enthalten einen der Verweistexte
  `wie ac`, `wie ge`, `wie dlg`, `analog ac`. Die Gruppen können sich
  überschneiden; die Zahlen bezeichnen Einträge, nicht Bilder oder nachgewiesene
  Konvertierungsfehler.
- Erneuerter Bestandsreview: 1.000 Einträge, 993 renderbare Paare; alle 48
  bisherigen Erfolgsvarianten bleiben unter der Reviewgrenze. Das ist ein
  Review vorhandener Ausgaben, kein frischer Lauf über alle 1.785 Bilder.
  Eine belastbare aktuelle Gesamtquote der autonomen Konvertierung ist damit
  weiterhin nicht belegt. Erledigte Aufgaben und bestandene Unit-Tests sind
  kein Ersatz für diese Quote.

## Neuester Fortschritt: AC0721

`AC0721_1_S` und alle fünf Farb-/Größen-Holdouts enthalten den ausdrücklich
beschriebenen Text `T`. Eigenständige XML-Beschreibungen und allgemeine
Konturregistrierung bringen alle sechs durch beide regulären Gates ohne
Pflichtmetrikregression. Die frische Zielmetrik sinkt von `3282.783936` auf
`481.410675`. Die sechs bereits akzeptierten P-Varianten behalten ihre SVGs.

67 fokussierte Tests bestehen; eine unabhängig entworfene SVG-Vorlage besteht
mit zwei Seeds jeweils 17/17 strenge Plan-B-CLI-Prüfungen. Die sechs
Bestandsschutztests sichern alle 31 Varianten ohne Regression. Fünf der sechs
Original-JPGs bestehen auch die strengere Plan-B-Prüfung; der große graue
Vordergrund-IoU-Fall bleibt als separate Aufgabe offen. Die Erfolgsübersicht
enthält jetzt 152 Bild-/SVG-Paare und bleibt vollständig im erweiterten
Rekonvertierungsprofil enthalten. Die erneute Archivkonvertierung besteht mit
152/152 Review-Pässen; die bekannte Drift bei 22 älteren Kompatibilitätsfällen
bleibt separat offen. Der vollständige Standardtestlauf besteht mit 2.116
Tests und 30 Profil-/Windows-Skips. Details und Abschlussnachweis:
[AC0721](next_arbeitspaket_2026-10-10_ac0721_1_s.md).

## Vorheriger Fortschritt: AC0713 und Erfolgsübersicht

`AC0713_1_L` und alle fünf Farb-/Größen-Holdouts enthalten jetzt auch Strich
und Punkt im Quadrat. Eigenständige Beschreibungen und die allgemeine
Rasterregistrierung für den oberen Griff bringen alle sechs durch beide
regulären Gates ohne Pflichtmetrikregression. Die Zielmetrik sinkt von
`1972.475586` auf `120.847115`; eine unabhängige Plan-B-Vorlage besteht
Original plus 16 Zufallsvarianten (17/17). 90 fokussierte Tests bestehen.

146 nachgewiesene Bild-/SVG-Paare sind mit ihren Beschreibungen und
Qualitätswerten separat unter `artifacts/satisfactory_conversions/` abgelegt.
Das erweiterte Profil konvertiert alle Einträge erneut aus Wegwerfkopien und
prüft die bestehende Reviewgrenze. Der strengere 31-Fälle-Bestandsschutz
bleibt separat. Der Review über 1.000 Einträge erhält alle 48 bisherigen
Erfolgsvarianten unter der Grenze. Details:
[AC0713 und Erfolgsübersicht](next_arbeitspaket_2026-10-10_ac0713_1_l.md).

## Vorheriger Fortschritt: AC0413

Das nächste dokumentierte Ziel war `AC0413_1_M`. Die Platzhalterbeschreibungen
verschwiegen Kreis, zwei schräge Linien und das aus Strichen aufgebaute T.
Auch eine zutreffende Beschreibung wurde zunächst als Buchstaben-Badge
fehlklassifiziert und mit dem voreingestellten `M` ausgegeben.

Die Beschreibungen sind jetzt eigenständig. Die neue allgemeine Registrierung
bestimmt Kreis, vier Linien und Farben aus dem Raster. Alle neun roten, grünen
und grauen Größenvarianten bestehen beide regulären Qualitätsgates ohne
Pflichtmetrikregression. Ein unabhängiges synthetisches SVG besteht mit zwei
Seeds jeweils Original plus 16 Zufallsvarianten. Die Prüfung dünner Linien
reagiert jetzt konsistent auf Verschiebungen zwischen Pixelmitten.

Grenzen bleiben ausdrücklich sichtbar: diese Registrierung unterstützt die
beschriebene Kreis-/Linienstruktur, keine beliebigen neuen Innenzeichen. Drei
graue JPGs verfehlen die zusätzliche strengere Vordergrund-IoU-Prüfung.
Der zufällige Gesamtpool und der ältere U-Bogen-Stresstest bleiben offen.
Details und Reproduktion: [Arbeitspaket](next_arbeitspaket_2026-10-10_ac0413_1_m.md).

## Konsequenz für die weitere Arbeit

Die bestehende Priorität bleibt: möglichst viele Motive in guter Qualität
erschließen, danach das Produkt vereinfachen. Als nächstes reguläres Paket folgt
`AC0711_1_M`. Für einen nachprüfbaren Stand zur Autonomie ist außerdem ein
frischer Kataloglauf mit zutreffenden Beschreibungen, unveränderten Gates und
getrennten Ergebnissen für erfolgreiche, verbesserbare und zurückgestellte
Bilder nötig. Solange dieser fehlt, wäre die Aussage „der ganze Katalog läuft
bereits zuverlässig ohne Entwicklungsarbeit“ nicht gerechtfertigt.
