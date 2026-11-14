# Zwei Linien und zwei Dreiecke

Der Benutzerauftrag zu AC0024.jpg (35 × 111 Pixel) wurde im Webauftrag
`33a0436e1b6d47dea9657742847ebc89` als gerahmtes Panel rekonstruiert.
Das blaue Dreieck fehlte; mehrere graue Konturen kamen hinzu.

Die Beschreibung „Dreieck zeigt nach oben/unten“ erreichte den vorhandenen
nativen Linien-/Dreieck-Fit nicht, weil dieser „Spitze nach …“ verlangte.
Zusätzlich erkannte die Zuordnung nur „links/rechts“, keine Adjektive wie
„linke/rechte“. Die begrenzte Sprachnormalisierung versteht jetzt die neue
Formulierung sowie die Tippfehler „Dreick“ und „Dreiek“. Zitierte Beschriftungen
bleiben unverändert. Die Farbprüfung versteht auch „Die linke Linie und das
linke Dreieck ist rot“. Widersprüchliche Farben/Richtungen werden abgelehnt.

Der frische Webauftrag `c411de58b31c4c3db61d489ddcbadca3` verwendet bytegleiche
Originalpixel und dieselbe Benutzerbeschreibung einschließlich Tippfehlern.
Er besteht nach 32,1 Sekunden die Qualitätsprüfung. Das gespeicherte SVG
enthält genau zwei schmale Rechtecke als Linien und zwei Dreiecke: links rot
nach oben, rechts blau nach unten. Es enthält keine zusätzlichen Konturen,
Hintergrundobjekte oder eingebetteten Rasterdaten. Der alte Auftrag bleibt
erhalten; das neue Ergebnis wurde automatisch als
`artifacts/converted_images/converted_svgs/AC0024.svg` abgelegt.

Die unveränderten Pixelgrenzen werden mit beiden Renderern erfüllt:

| Prüfung | Vorher MuPDF | Nachher MuPDF | Nachher librsvg |
| --- | ---: | ---: | ---: |
| Normalisierter Pixelfehler | 0,006426 | 0,001585 | 0,001678 |
| Vordergrund-IoU | 0,7372 | 0,9700 | 0,9685 |
| Konturausrichtung | 0,8247 | 0,9909 | 0,9903 |

`summary.json` enthält Quellhashes, Vorher-/Nachher-Prüfwerte und den vollständigen
Webauftrag. `preview.png` zeigt Original, bisherigen Entwurf und Verbesserung.
`verify.py` prüft beide gespeicherten Ergebnisse erneut und erzeugt die Belege:

```powershell
.venv/Scripts/python.exe artifacts/evaluation/arrow_pair_2026-11-14/verify.py
.venv/Scripts/python.exe -m pytest -q tests/test_arrow_pair_runtime.py tests/test_description_language.py tests/detailtests/test_dual_arrow_runtime_helpers.py
```

Die drei genannten Testmodule bestehen mit 95 Tests; die beiden zusätzlichen
Prüfungen zur Beschreibungsvererbung bestehen ebenfalls (insgesamt 97 Tests).

Die Änderung erweitert die unterstützte Beschreibungssprache des bestehenden
Rot-/Blau-Paarmodells. Sie verändert weder Geometrievorlagen noch Qualitätsgrenzen
und benötigt keine bildnamenabhängigen Koordinaten oder Referenz-SVGs.
