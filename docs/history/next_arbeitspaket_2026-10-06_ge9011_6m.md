# Arbeitspaket – GE9011_6M Pfeil mit Verlaufsschaft (2026-10-06)

Der nächste offene Plan-B-Kandidat ist auf dem neuen Branch
`codex/ge9011-quality-2026-10-06` abgeschlossen.

## Ursache und Beschreibung

Die XML beschrieb sämtliche Farb- und Größenvarianten als „Wie BackBottom:
hellgraues Quadrat“. Die Raster zeigen dagegen eine gefüllte Dreieckspitze
über einem schmaleren, vertikalen Rechteckschaft mit horizontalem Helligkeitsverlauf
und weißem Abstand. Die neue gemeinsame Beschreibung benennt genau diese
Topologie, ohne Katalogreferenzen, numerische Geometrie oder feste Farben.
Der historische Kandidatenwert `15528.650391` ist keine kontrollierte Baseline.
Das frisch erzeugte Vorlauf-CLI-SVG erreicht `15406.099609`.

## Allgemeiner Algorithmus

`imageCompositeConverterGradientArrow.py` registriert einen ausdrücklich nach
oben beschriebenen Pfeil mit dreieckiger Spitze und Verlaufsschaft. Die weißen
Rasterzeilen trennen die beiden Regionen. Zwei Geradenregressionen bestimmen
die Dreieckskanten und deren Schnittpunkt. Die zeitlich unveränderte horizontale
Farbverteilung des Schafts liefert dessen Lage, Breite und native SVG-Verlaufstopps;
die Zahl der Stopps ist auf neun begrenzt. Rasterkonturen werden nicht exportiert.

Eine deterministische Suche mit höchstens 73 Renderproben variiert die neun
Geometrieparameter und drei globale Verlaufskanäle. Diese Farbsuche korrigiert
den Renderunterschied zwischen beobachteter Farbe und SVG-Verlauf und erhält
dessen hellere Mitte. Die Topologie bleibt erhalten. Nur endliche, strikt kleinere
Renderfehler werden akzeptiert; die Eingabepixel bleiben unverändert.
Die Runtime verwendet diesen Pfad vor Sample-Abfragen und generischem Fitting.
Das gespeicherte SVG enthält einen weißen Hintergrund, ein Dreieck und einen
Rechteckschaft mit nativem horizontalem Linearverlauf; kein eingebettetes Raster.

Die nachgewiesene Registrierung ist auf eine nach oben gerichtete, ausreichend
breite Dreieckspitze und einen darunterliegenden, schmaleren, flachen Verlaufsschaft
mit weißem Abstand begrenzt. Gedrehte Pfeile, beliebige Hintergründe und gekrümmte
Schäfte sind nicht nachgewiesen. JPEG- und Antialiasing-Restfehler sowie die
bestehenden CLI-Warnungen über konzentrierte Fehler bleiben sichtbar.

## Harte Abnahme am gespeicherten CLI-SVG

Ziel und 13 Größen-/Farb-Holdouts werden mit fremden Dateinamen, Seed 0,
`semantic-only` und derselben Toolchain verarbeitet. Der Vorlauf verwendet die
ursprüngliche XML und deaktiviert ausschließlich die neue Registrierung.
Der Nachlauf verwendet die eigenständige Beschreibung und Rasterregistrierung.
Somit misst die Abnahme die vollständige Daten- und Algorithmuskorrektur.

| Variante | mean_delta2 vorher | mean_delta2 nachher | Edge-Alignment | Masken-IoU |
|---|---:|---:|---:|---:|
| GE9011_1M | 13200.658203 | 491.186676 | 0.883336 | 1.000000 |
| GE9011_1S | 10592.226562 | 374.383331 | 0.885292 | 1.000000 |
| GE9011_2M | 12514.060547 | 458.077515 | 0.854143 | 1.000000 |
| GE9011_2S | 8246.426758 | 304.739990 | 0.878417 | 1.000000 |
| GE9011_3M | 8046.264160 | 280.999176 | 0.788474 | 0.935943 |
| GE9011_3S | 4886.603516 | 180.856674 | 0.866689 | 1.000000 |
| GE9011_4M | 4289.804199 | 127.860832 | 0.787874 | 0.981735 |
| GE9011_4S | 2101.856689 | 56.889999 | 1.000000 | 0.872483 |
| GE9011_5M | 8173.620117 | 314.489166 | 0.912399 | 0.932384 |
| GE9011_5S | 6300.600098 | 279.906677 | 0.857984 | 1.000000 |
| GE9011_6M | 15406.099609 | 500.660004 | 0.802808 | 0.932384 |
| GE9011_6S | 10710.790039 | 463.696655 | 0.881105 | 1.000000 |
| GE9011_7M | 12312.446289 | 233.709167 | 0.932249 | 0.932384 |
| GE9011_7S | 11147.962891 | 174.713333 | 0.866434 | 1.000000 |

Alle 14 Fälle bestehen beide unveränderten Qualitätsgates. Jede Pflichtmetrik
verbessert sich oder bleibt unverändert gegenüber dem kontrollierten Vorlauf.
Der unabhängige SVG-Semantikcheck verlangt Dreieck, engeren Schaft, weiße Trennung,
hellere Verlaufsmitte und korrekte Richtung. Falsche Richtung, Überlappung,
falsche Verlaufsachse, flache Füllung, zusätzliche Primitive, Transformationen
und eingebettete Raster werden abgelehnt. Ein identisch gerendertes PNG/SVG-Paar
kalibriert sämtliche Pflichtmetriken auf die Idealwerte.

## Perception-Lerneffekt: generalisiert

Sieben Farbvarianten in zwei Größen bestehen ohne Katalogwissen beide Gates.
Synthetische Varianten sichern zwei weitere Farben, verschobene Lage und doppelte
Größe. Fehlende Spitze, fehlender Schaft, Löcher, flache Schaftfarbe und
widersprüchliche Beschreibungen werden verworfen. Konstante und nicht endliche
Fehler liefern keine akzeptierte Registrierung. Ein Runtime-Test verbietet
Sample-SVG-Zugriff und Raster-Embedding und belegt identische SVGs nach Umbenennung.

## Belege, Reproduktion und Abschluss

`artifacts/evaluation/gradient_arrow_recheck_v1/` enthält Manifest mit
Quellhashes und Toolchain, versiegelte Baseline, 28 eingefrorene CLI-SVGs,
CLI-Logs, Gatebericht und Reproduktionsbeleg. Zwei unabhängige CLI-Läufe erzeugen
exakt dieselben 28 SVG-Bytes und sämtliche Gateentscheidungen.

```bash
python -m tools.run_gradient_arrow_recheck \
  artifacts/evaluation/gradient_arrow_recheck_v1/manifest.json \
  --output-dir .tmp/gradient-arrow-reproduction
python -m tools.evaluate_gradient_arrow_recheck \
  artifacts/evaluation/gradient_arrow_recheck_v1/manifest.json \
  --output .tmp/gradient-arrow-gates.json
python -m compileall src tests tools
python -m pytest -q
python -m src.imageCompositeConverter --help
python -m tools.check_no_new_image_id_hardcoding
```

Die 37 fokussierten Tests sind grün. Das vollständige Defaultprofil meldet
`1593 passed, 29 skipped` ohne Warnungen.
Die 29 bestehenden Windows-Skips betreffen POSIX-Shell-Integration. Syntaxprüfung,
CLI-Help-Smoke und Runtime-ID-Nullprüfung sind grün (`0 occurrences`).
Die isolierte Umgebung verwendet CPython 3.12.14, NumPy 2.5.3, OpenCV 4.14.0
und PyMuPDF 1.26.7. Zwei anfängliche Unterprozessfehler im Gesamttest stammen
vom Windows-PYTHONPATH-Aufbau; ein korrigierter temporärer Bootstrap lädt die
kompatiblen Bibliotheken vor der historischen Linux-Vendor-Auswahl.

Der erneuerte Review enthält 688 Einträge mit 684 renderbaren Paaren; vier bereits
fehlende SVG-Paare bleiben markiert. Die separat belegten Gate-Passes einschließlich
aller 14 Pfeilvarianten sind aus der Kandidatenauswahl ausgeschlossen, weil die
historische Sammelausgabe weiterhin alte SVGs enthält. Der vollständige Aufruf
steht in `review_reproduction_2026-10-06.json`. Die nächste Rotation beginnt mit
**GE0281**, gefolgt von GE0300, GE1420_S, AC0403_1_L und AC0130_S. Vor der
Nachzeichnung ist jeweils eine frische CLI-Baseline zu prüfen.
