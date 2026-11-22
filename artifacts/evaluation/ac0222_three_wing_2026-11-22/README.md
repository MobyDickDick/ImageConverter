# Drei Ventildreiecke und quadratisches Stellglied

Das gemeldete SVG enthielt ein grosses graues Quadrat und eine weisse Diagonale.
Ventildreiecke, Griff und die zweite Stellglieddiagonale fehlten. Die aktuelle
Beschreibung benennt alle Teile bereits und blieb in beiden XML-Tabellen
byteidentisch erhalten.

## Ursachen und Korrektur

Die allgemeine Inventarauswertung erkannte die gebeugte Mehrzahl „Dreiecken“
nicht. Der anschliessende allgemeine Geometry-IR-Pfad interpretierte die
Beschreibung als Quadratpanel. Auch die beiden Quadratdiagonalen und der
Griff waren im ermittelten Inventar nicht vollständig enthalten. Die
Beschreibungskontrolle konnte den unvollständigen Entwurf deshalb zulassen.

Die allgemeine Zählung unterstützt jetzt auch die entsprechenden Dativformen
von Kreis, Rechteck, Quadrat und Dreieck. Eine geschlossene Auswertung der
beschriebenen Ventilkonstruktion erklärt vor jedem Bildzugriff drei Dreiecke,
eine Linie, ein Quadrat und zwei Diagonalen. Sie wählt die numerische Anpassung
dieser vollständigen Geometrie und verwirft das unpassende Panelmodell.
Die Suche passt native Formen und Grauverläufe mit dem vorhandenen gemeinsamen
Suchbudget an die Bildpixel an. Es gibt keine Bildnamen-Sonderregel, keine
Referenzvektoren und keine zusätzliche Restlinienrekonstruktion.

Vorlagen und Entwürfe müssen ebenfalls die gemeinsame Spitze, die linke,
obere und untere Dreiecksbasis, den waagerechten Griff bis zur linken
Quadratmitte, ein echtes Quadrat, beide Eckdiagonalen und die beschriebenen
Grautöne samt Verlaufsrichtung einhalten. Fehlende Teile werden auch in
fehlgeschlagenen Entwürfen abgewiesen. Die GUI-Prüfversion ist auf 14 erhöht,
damit ältere gespeicherte Ergebnisse erneut geprüft werden.

## Gespeichertes Ergebnis und Bedienweg

Der echte GUI-Worker `a34933b7ae764837bb3d149380612cb2` verwirft das alte
SVG mit `three_wing_valve_incomplete`. Mit unveränderter Beschreibung und
Seed 2026 entsteht in 12,7 Sekunden ein bestandenes Ergebnis. Die reguläre
Projektablage speichert es unter
`artifacts/converted_images/converted_svgs/AC0222_L_sia.svg`.

Der HTTP-Lauf `ec47562af20a4763be87c089c184b021` auf dem aktualisierten
Webserver sucht ohne Wiederverwendung des Projekt-SVGs erneut. Er besteht in
14,6 Sekunden nach 339 Renderkandidaten mit demselben Ergebnis. Die automatische
Katalogaktualisierung meldet `pixel_pass`. Der Webserver auf Port 8766 wurde
nach Prüfung auf laufende Arbeiten neu gestartet; der Hintergrunddienst war
gestoppt. Alte Fehlversuche bleiben als Historie erhalten.

| Prüfung des gespeicherten SVGs | MuPDF | unabhängiges librsvg |
| --- | ---: | ---: |
| Normalisierter Pixelfehler | 0,00061341 | 0,00066777 |
| Vordergrundfehler | 0,00142302 | 0,00157207 |
| Vordergrund-IoU | 0,97137150 | 0,97647849 |
| Kantenübereinstimmung | 0,93181276 | 0,90422845 |
| Bildprüfung | bestanden | bestanden |

Die Qualitätsgrenzen bleiben unverändert. Das SVG enthält acht native
Zeichenelemente, darunter drei geschlossene Dreieckspfade, und bleibt innerhalb
75 × 50 Pixeln. `summary.json` enthält Messwerte und Worker-/HTTP-Nachweise.
`comparison.png` zeigt lokal Original, vorheriges SVG und korrigiertes SVG
mit dem unabhängigen Renderer. Rohdaten und alte Entwürfe bleiben lokal.

## Tests und Grenzen

70 fokussierte Tests bestehen: 29 neue Tests zu Inventar, Verbindungen,
Vorlagen-/Entwurfsverletzungen, Farben und Verlauf, unabhängig erstellten
Geometrien in zwei Grössen sowie einem echten GUI-Worker mit neutralem
Dateinamen; hinzu kommen bestehende Form-, Vorlagen-, Dreiweg- und GUI-Tests.

Die breitere Prüfung ergibt 155 bestandene Tests und fünf Fehler. Alle fünf
Fehler treten auch bei Ausführung der vier betroffenen Konvertierungsmodule
aus `git show HEAD` unverändert auf: zwei alte Checkpoint-Erwartungen,
zwei Zweiwegventil-GUI-Erwartungen und eine Canvas-Modellprüfung. Sie werden
hier nicht als behoben ausgewiesen. Die Prüfung gegen Bild-ID-Sonderfälle
und `git diff --check` bestehen.

Die neue Sprachauswertung ist begrenzt: Sie unterstützt die dokumentierte
vollständige Konstruktion mit Dreiecken links/oben/unten und Quadrat rechts.
Zusätzliche oder widersprüchliche Sätze werden nicht ignoriert. Andere
Stellglieder, Anordnungen und beliebige Umschreibungen sind damit nicht
allgemein gelöst. Die freie Grundformensuche unterstützt diese Beschreibung
weiterhin nicht; die normalen Profile verwenden die vollständige Anpassung.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_three_wing_valve_description.py tests/test_simple_form_representation.py tests/test_sample_start_regression.py tests/test_three_way_valve_runtime.py -q
.venv/Scripts/python.exe -m pytest tests/test_image_converter_gui.py::test_free_search_rejects_unsupported_claim_before_launch tests/test_image_converter_gui.py::test_free_search_profiles_reach_cli_with_durable_memory_and_skip_samples -q
.venv/Scripts/python.exe tools/check_no_new_image_id_hardcoding.py
git diff --check
```
