# AC0201: Kreis mit zwei symmetrischen Innenlinien

Der gemeldete Startabbruch ist behoben. Die alten GUI-Aufträge
`c1eae919d889470a9ad60b7df81839df` und `c709ea88f9374841946b78863024faaa`
brachen mit `insufficient_description_no_raster_fallback` ab. Ihre Beschreibung
erzeugte keine Geometry-IR; es gab kein einziges Rendering. Die vollständige
Inventarprüfung verlangte bereits einen Kreis und zwei Linien, aber es fehlte
ein dafür erreichbares Beschreibungsmodell.

Zusätzlich widersprach die horizontale Symmetrieachse im Text dem Original.
Nach ausdrücklicher Zustimmung des Benutzers wurde ausschliesslich der Eintrag
für `AC0201.jpg` in beiden gepflegten XML-Tabellen auf die senkrechte Achse
korrigiert. Dabei wurden auch `dunelgraue` und `welches` berichtigt.

Die ergänzte begrenzte Beschreibungsauswertung erklärt vor der Rastermessung
einen Kreis und zwei gespiegelte Geraden. Sie unterstützt beide Achsen und
verwirft zusätzliche, nicht verstandene Aussagen. Kreisposition, Radius,
Linienendpunkte, Strichbreiten und Grautöne werden am Eingabebild angepasst.
Die zweite Linie entsteht durch Spiegelung der ersten. Es werden keine
Restformen, Referenz-SVGs oder Bildnamen zur Konstruktion verwendet.
Die bestehende gemeinsame Registrierung erfasst Renderbudget, Seed und Deadline.
Auch spätere Vorlagenänderungen müssen beide Linien innerhalb des Kreises und
die beschriebene Symmetrie erhalten.

## Tatsächliches Ergebnis und offene Qualitätsgrenze

Der echte `Jobs.upload`-/`Jobs.start`-Worker erstellt mit Profil `quick`, Seed 42
und ohne SVG-Vorlage ein vollständiges SVG. Der wiederholte Lauf benötigt
11,3 Sekunden und erhält dieselbe bereits gespeicherte Projektversion:

`artifacts/converted_images/converted_svgs/AC0201.svg`

Die unabhängige Nachprüfung bestätigt Inventar, Symmetrie und die ursprünglichen
50 × 50 Pixel grossen Zeichengrenzen. **Die Rasterprüfung besteht noch nicht.**
Das SVG wird korrekt als Entwurf mit `quality=warning` gespeichert.

| Prüfung | Ergebnis | Bestehensgrenze |
| --- | ---: | ---: |
| Normalisierter Pixelfehler | 0,00045539 | höchstens 0,01 |
| Vordergrundfehler | 0,00128112 | höchstens 0,04 |
| Vordergrund-IoU | 0,83613 | mindestens 0,85 |
| Kantenübereinstimmung | 0,97563 | mindestens 0,72 |

Die Qualitätsgrenzen wurden nicht geändert. Der Abbruch ohne Ergebnis und die
falsche Beschreibung sind korrigiert; eine vollständig bestandene Konvertierung
dieses JPEGs ist damit ausdrücklich noch nicht nachgewiesen.
`comparison.png` zeigt links das Original und rechts das SVG.
`summary.json` enthält den Worker- und Speichernachweis, `saved_quality.json`
die unabhängige Prüfung der gespeicherten Datei.

## Prüfungen

17 neue Tests bestehen: Katalogkorrektur, Inventar vor Rasterzugriff,
synthetische Geometrien für beide Achsen und zwei Grössen, fehlende Linien,
falsche Spiegelung, überstehende Endpunkte, verformter Kreis, gemeinsame
Transformation, zusätzliche Aussagen, geschützte Textlabels sowie ein echter
GUI-Worker mit neutralem Dateinamen. Die vier unabhängigen synthetischen Fälle
bestehen auch die unveränderte Rasterprüfung.

Die erweiterte bestehende Auswahl ergibt 123 bestandene und fünf fehlgeschlagene
Tests. Drei Fehler der bestehenden Checkpoint-/Canvas-Tests wurden auch mit den
beiden geänderten Laufzeitmodulen aus `HEAD` reproduziert. Zwei bestehende
Ventiltests mit alter SVG-Vorlage liefern weiterhin eine Warnung; ihre Ursache
wurde in dieser Reparatur nicht geändert. Die gesamte Auswahl ist daher nicht
grün. Die Bild-ID-Nullprüfung und `git diff --check` bestehen.

```powershell
$env:PYTHONPATH='.'
.venv/Scripts/python.exe artifacts/evaluation/ac0201_circle_lines_2026-11-21/run_gui.py
.venv/Scripts/python.exe -m pytest tests/test_symmetric_circle_lines_description.py -q
.venv/Scripts/python.exe tools/check_no_new_image_id_hardcoding.py
git diff --check
```

Der laufende Webserver wurde nicht neu gestartet, da er andere Aufträge
verarbeitet. Nach deren Abschluss ist ein Neustart nötig, damit auch sein
bereits importierter Beschreibungsprüfer die neue Symmetrieprüfung übernimmt.
