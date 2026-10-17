# AC0840 und begrenzte alternative Suche (2026-10-17)

Das nächste reguläre Arbeitspaket nach AC0424 war `AC0840_S`, gefolgt von
`AC0840_M`. Die ganze Familie mit S/M/L wurde gemeinsam bearbeitet. Alle drei
gespeicherten SVGs bestehen beide unveränderten regulären Qualitätsgates ohne
Pflichtmetrikregression und zusätzlich das strenge Plan-B-Pixelgate. Eine
unabhängig konstruierte blaue Kreisscheibe mit anderer Beschriftung `pH`,
anderer Größe, Lage und Palette besteht Original plus 16 Variationen: **17/17**.

## Ursache und Korrektur

Die bisherige Beschreibung führte zu einem groben Kreis-/Textbadge. Der
vorhandene gute Rasterfit für einen einzelnen Großbuchstaben unterstützte den
gemischten Kurztext nicht. Die ursprünglichen Rasterdateien und die alte
Beschreibung wurden vor der Änderung durch echte CLI-Läufe vermessen.
Ein fremder Dateiname verhindert dabei den Zugriff auf Katalogwissen.

Die beiden XML-Kataloge beschreiben nun eigenständig eine einfarbige hellgraue
Kreisscheibe mit Rand und mittigem `rF`. Die neue allgemeine Registrierung
unterstützt explizit beschriebene alphanumerische Kurztexte aus zwei bis vier
Zeichen. Sie bestimmt Kreis, Farbe, Kontur und Schriftposition aus dem Raster
und prüft vier alternative Modelle: normal/fett und gemeinsamer Textzug/
einzeln positionierte Zeichen. Eine Silhouettenprüfung verwirft falsche Texte
und zusätzliche Rasteranteile. Es gibt keine Bildkennungen oder Referenz-SVGs
im Produktionsalgorithmus.

## Messwerte der tatsächlichen gespeicherten CLI-Ausgaben

| Raster | Mean-Delta² vorher | Mean-Delta² nachher | Vordergrund-IoU nachher | Strenges Gate |
|---|---:|---:|---:|:---:|
| AC0840_S | 8802,440430 | 447,333344 | 0,877863 | bestanden |
| AC0840_M | 7016,399902 | 228,524994 | 0,932642 | bestanden |
| AC0840_L | 7071,016602 | 464,736664 | 0,937008 | bestanden |

Die unveränderten Quellenhashes, die Originalbeschreibung, CLI-Logs, alten und
neuen SVGs stehen unter `artifacts/evaluation/conversion_search_2026-10-17/`.
`acceptance.json` wird aus den gespeicherten Vektoren unabhängig neu berechnet.
Der SVG-Zugriffswächter meldet null verbotene Referenzzugriffe. Der neue
unabhängige Semantikprüfer verlangt genau Kreis, Hintergrund und den richtigen
Text, auch wenn dessen Zeichen einzeln gesetzt sind.

Eine Ablation mit neuer Beschreibung und neuen Textmodellen, aber ohne
zusätzliche Parametersuche, besteht ebenfalls 3/3. Sie reproduziert die
abgenommenen Pixelwerte. Der wesentliche Qualitätsgewinn dieser Familie kommt
somit von zutreffender Beschreibung und Modellvergleich. Zusätzliche Neustarts
sind hier nach Erreichen des lokalen Pixelgates unnötig. Das vorläufige
`final/`-Experiment verfeinerte weiter, verbrauchte aber mehr Prüfungen; es ist
nicht die archivierte Abnahme. Die zwei anfänglichen Ausführungsfehler bleiben
unter `after/` und `after_v2/` als Diagnose erhalten und zählen nicht als Erfolg.

Ein erneuter Lauf auf dem endgültigen Code (`replay/`) reproduziert die drei
abgenommenen SVGs und Messwerte. Laufzeiten bei gleichzeitig laufenden Tests
belegen keine allgemeine Beschleunigungsquote. Ein falsches Ergebnis des alten
Wegs entstand in etwa einer Sekunde; die vier neuen Modelle erfordern zunächst
mehr Arbeit. Rendercache, Budget und das Überspringen bereits genauer Fits
begrenzen die zusätzliche Suche.

## Allgemeine Suchverbesserung und erhaltene Erfahrung

Die CLI aktiviert standardmäßig das Suchportfolio. Analytische Fits mit
verfehltem lokalem Pixelgate können drei begrenzte alternative Suchtrajektorien
ausprobieren. Gleiche SVG-Kandidaten werden innerhalb einer Registrierung
zwischengespeichert. Ein zufälliges Verschieben der fertigen Non-Composite-
Ausgabe ist standardmäßig abgeschaltet. Suchdiversität erfolgt vor der Auswahl.

Seeds, Vorschläge, tatsächliche Renderzahlen und Fortschritte bleiben sichtbar.
Geprüfte Kurztextvarianten werden mit getrennter lokaler Semantik- und
Pixelbewertung gespeichert. Nur im Modus `standard` darf die Statistik
erfolgreicher Modelle und Suchwege künftige Versuche priorisieren. Sie lädt keine
fertige SVG-Vorlage. `semantic-only` liest keine solche Erfahrung.

Das ist eine begrenzte erste Lernschleife. Eine automatische Entwicklung neuer
Szenentopologien oder selbstständige Codeänderung ist damit nicht umgesetzt.
`GENERAL-SCENE-01` und die vollständige Inventur älterer Fehleraufgaben bleiben
offen. Der verbindliche Nachbearbeitungsprozess steht in
[plan_b_learning_workflow.md](plan_b_learning_workflow.md); drei Diagramme in
[conversion_search_uml.md](conversion_search_uml.md) zeigen Laufzeit und Entwicklung.

## Bestand und nächste Rotation

Nur die drei abgenommenen AC0840-Größen wurden dem Archiv hinzugefügt:
**355 Paare**, alle 352 bisherigen Indexeinträge und deren Bilder/SVGs unverändert.
Der erneuerte Bestandsreview enthält weiter 1.000 Einträge und 993 renderbare
Paare; alle 48 bisherigen Bestenlisteneinträge bleiben unter ihrer Reviewgrenze.
Frühere Ausschlüsse bleiben erhalten. Nächste reguläre Rotation:
`SE0082`, `AC0411_1_M`, `AC0910_L`, `GE0204_M`, `AC0921_M`.

Das vollständige Abschlussprofil deckt alle **3.341 gesammelten Testknoten
genau einmal** ab: **3.311 bestanden, 30 regulär übersprungen, null Fehler**.
Die vier frischen Prozesse, ihre unveränderte vollständige Sammlung und das
zusammengeführte XML sind in `standard_profile_summary.json` und
`standard_profile.xml` nachgewiesen. Zusätzlich bestehen die 188 gezielten Tests,
`compileall`, CLI-Hilfe, Bild-ID-Hardcoding-Nullprüfung und `git diff --check`.

Alle **352 bisherigen Archivbilder** wurden mit der echten CLI erneut
konvertiert und unabhängig vermessen. Alle bestehen die bisherige absolute
Archiv-Pixelgrenze. Gegenüber dem vorherigen echten CLI-Archivlauf sinkt
Mean-Delta² bei **12 Fällen**, bleibt bei **340 gleich** und steigt bei **keinem**.
Die neuen drei Fälle bestehen darüber hinaus ihre oben dokumentierten regulären
und strengen Gates. Die Archivgrenze ist eine andere Prüfung; der Archivlauf
belegt keine vollständige neue semantische Abnahme aller bestehenden Motive.
Die historischen Abweichungen gegenüber gespeicherten Bestresultaten bleiben
im Bericht getrennt sichtbar. Die Bestresultate selbst wurden nicht ersetzt.

Der erste Standard-Archivlauf brach beim Schreiben von `conversion_bestlist.csv`
mit Windows-`OSError 22` ab. Eine frische Wiederholung der 48 betroffenen Fälle
in einem kürzeren Ausgabepfad besteht 48/48. Der erste Fehlerbericht und das Log
bleiben unter `diagnostics/` erhalten. Der Abschlussbericht verbindet ausschließlich
die tatsächlich abgeschlossenen 304 semantischen und 48 Standardkonvertierungen.
Alle 352 neuen SVGs, ihre Hashes und der Vergleich stehen in
`archive_recheck.json` und `archive_reconverted_svgs/`. Der Verifikator rendert
sie ohne neuen Konverterlauf unabhängig erneut.

## Reproduktion

```powershell
.venv/Scripts/python.exe artifacts/evaluation/conversion_search_2026-10-17/verify_evidence.py
.venv/Scripts/python.exe -m tools.evaluate_short_label_search artifacts/evaluation/conversion_search_2026-10-17
.venv/Scripts/python.exe -m tools.evaluate_conversion_search --image artifacts/images_to_convert/AC0840_S.jpg --image artifacts/images_to_convert/AC0840_M.jpg --image artifacts/images_to_convert/AC0840_L.jpg --description-file artifacts/evaluation/conversion_search_2026-10-17/description.txt --output .tmp/short-label-replay --portfolio
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/conversion_search_2026-10-17/independent.svg --description-file artifacts/evaluation/conversion_search_2026-10-17/independent.txt --seed 20261017 --output-dir .tmp/short-label-independent --keep-debug-artifacts
.venv/Scripts/python.exe -m pytest --basetemp .tmp/short-label-tests
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```
