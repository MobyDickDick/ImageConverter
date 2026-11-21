# AC0201_M: vollständiges motorgetriebenes Zweiwegventil

Die gespeicherte effektive Beschreibung nennt ein motorgetriebenes Zweiwegventil
mit horizontal angeordneten Ventilflächen, einer Kelle mit Griff nach unten und
zusammenhängendem Farbverlauf. Der bisherige Inventarparser verstand diese
zusammengesetzte Beschreibung nicht; die gespeicherte SVG-Datei enthielt nur
einen falsch platzierten Kreis. Die Beschreibung und beide XML-Tabellen wurden
bei dieser Reparatur nicht geändert.

Die ergänzte, begrenzte Beschreibungsauswertung erklärt die vollständige
Elementliste vor dem Bildabgleich: ein Kreis, eine Linie und zwei Dreiecke.
Der erste Beschreibungsfit bestimmt Lage, Grösse und Farben am Rasterbild und
passt ausschliesslich diese Formen an. Beide Dreiecke besitzen dieselbe Spitze
und teilen einen Verlauf in Benutzerkoordinaten. Die dauerhafte SVG-Prüfung
prüft diese Verbindung, den senkrechten Motorgriff und den gemeinsamen Verlauf
auch bei späteren Vorlagenanpassungen. Zusätzliche oder widersprüchliche
Beschreibungssätze werden vom begrenzten Vertrag nicht stillschweigend ignoriert.

Die Auswahl hängt vom vollständigen unterstützten Beschreibungstext ab;
Produktionscode enthält keine Bild-ID oder Referenz-SVGs. Die entfernte zweite
Rasterrekonstruktion bleibt ausgeschaltet. Andere Ventilorientierungen,
Beschriftungen, quadratische Motoren und beliebige freie Umformulierungen sind
durch diesen ergänzten Vertrag nicht allgemein unterstützt.

## Ergebnis im echten GUI-Worker

Ein erster Lauf über `Jobs.upload` und `Jobs.start` mit Profil `quick`, Seed 42
und der vorhandenen Kreisvorlage verwirft diese mit
`logical_object_count:line:1:0`. Der normale erste Beschreibungsfit startet und
liefert ein bestandenes SVG. `stale_template_summary.json` dokumentiert diesen
Lauf. Ein anschliessender frischer Lauf ohne Vorlagenwiederverwendung liefert
das abschliessend geprüfte und regulär im Projekt gespeicherte Ergebnis:

`artifacts/converted_images/converted_svgs/AC0201_M.svg`

| Prüfung | Alte Kreisvorlage | Abschliessendes gespeichertes SVG |
| --- | ---: | ---: |
| Normalisierter Pixelfehler | 0.03543055 | 0.00036517 |
| Vordergrund-IoU | 0.22955 | 0.95797 |
| Kantenübereinstimmung | 0.32924 | 0.94033 |
| Vollständige Elementliste | nein | ja |
| Qualitätsprüfung | ungenügend | bestanden |

Die Ausgabe liegt vollständig innerhalb der ursprünglichen 30 × 40 Pixel.
Die reguläre Projektablage sichert vorherige SVG-Versionen in `gui_history`.
`gui_summary.json` dokumentiert den frischen Lauf, `saved_quality.json` die
unabhängige erneute Prüfung des gespeicherten SVGs. `comparison.png` zeigt links
das Original und rechts das gerenderte Ergebnis, achtfach als Pixel vergrössert.
Das Ergebnis ist eine bestandene Annäherung an das kleine JPEG.

## Reproduktion und Prüfstand

```powershell
$env:PYTHONPATH='.'
.venv/Scripts/python.exe artifacts/evaluation/ac0201_motor_valve_2026-11-21/run_gui.py --fresh
.venv/Scripts/python.exe -m pytest tests/test_two_way_valve_description.py tests/test_description_language.py tests/test_sample_start_regression.py tests/test_simple_form_representation.py tests/test_canvas_containment.py -q
.venv/Scripts/python.exe tools/check_no_new_image_id_hardcoding.py
git diff --check
```

**122 Tests bestanden.** Abgedeckt sind der echte GUI-Start mit unpassender
Vorlage und neutralem Dateinamen, die vollständige Inventarprüfung, unabhängige
synthetische Geometrie mit anderen Farben und zwei Grössen, zusätzliche und
widersprüchliche Aussagen, zerstörte Verbindungen, gemeinsames Skalieren und
Verschieben sowie bestehende Sprach-, Vorlagen-, Grundformen- und Canvas-Prüfungen.
Die Nullprüfung für Bild-ID-Sonderfälle und `git diff --check` bestehen.

Der lokale Webserver auf Port 8766 wurde geprüft. Sein Hintergrunddienst
verarbeitete eine andere Konvertierung; er wurde deshalb nicht unterbrochen.
Für die laufende Oberfläche ist nach Abschluss beziehungsweise bewusstem
Beenden dieses Hintergrunddienstes ein Serverneustart nötig.
