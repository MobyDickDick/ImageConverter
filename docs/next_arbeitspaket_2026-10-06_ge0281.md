# Arbeitspaket – GE0281 radial schattierte Kugel (2026-10-06)

Die nächste dokumentierte Plan-B-Aufgabe ist auf
`codex/ge0281-quality-2026-10-06` abgeschlossen.

## Ursache und Datenkorrektur

Die XML beschrieb `GE0281` und `GE0282` als hellgraues Quadrat mit einer
Katalogreferenz. Beide Raster zeigen einen gefüllten Kreis mit heller Mitte
und dunklerem Außenbereich. Die beiden Einträge beschreiben diese Topologie
jetzt eigenständig und ohne numerische Geometrie oder feste Farbparameter.
Die Farbe wird aus dem Eingabebild bestimmt.

Der historische Sammelwert `15287.335938` ist keine kontrollierte Baseline.
Der frische, umbenannte CLI-Vorlauf mit ursprünglicher Beschreibung erreicht
`14981.222656`. Die Abnahme verwendet dieselbe Toolchain, Seed 0 und
`semantic-only`; ausschließlich die neue Registrierung wird im Vorlauf
deaktiviert. So werden Datenkorrektur und allgemeiner Algorithmus gemeinsam
gegen die tatsächliche bisherige CLI-Ausgabe geprüft.

## Allgemeiner Algorithmus

`imageCompositeConverterRadialDisk.py` registriert einen ausdrücklich
beschriebenen Kreis mit radialem Verlauf, heller Mitte und dunklerem
Außenbereich. Die größte Vordergrundkomponente liefert Rastergrenzen.
Eine algebraische Kreisregression bestimmt Mittelpunkt und Radius;
Konturpunkte werden nicht in das SVG exportiert. Radiale Zonen liefern
die Farben für sieben native SVG-Verlaufstopps. JPEG-Farbsaum und
Antialiasing am äußeren Rand dürfen dabei einen helleren Abschluss erzeugen;
die dunklere Außenregion wird unabhängig im inneren Außenband geprüft.

Eine deterministische Koordinatensuche mit höchstens 145 Renderproben
verfeinert Mittelpunkt, Radius und die drei Farbkanäle jedes Stopps.
Sie akzeptiert ausschließlich endliche, strikt bessere Renderfehler
und erhält Kreisgeometrie und hellere Mitte. Die schattierte Lösung muss
auch gegenüber einem aus denselben Pixeln abgeleiteten flach gefüllten
Kreis besser sein. Eingabepixel bleiben unverändert.

Zusätzliche Komponenten, deutlich elliptische oder unregelmäßige Formen,
Löcher, Innenmarkierungen, flache Farbe und widersprüchliche Beschreibungen
werden verworfen. Die Runtime führt die Registrierung vor Sample-Abfragen
und generischem Fitting aus. Der Pfad liest keine Dateinamen, Katalog-IDs,
Sample-SVGs oder gespeicherten Konvertierungsergebnisse.

Der bestehende private PyMuPDF-Radialadapter registriert den SVG-Namensraum
jetzt auch selbst. Zuvor konnte eine reine Radialdarstellung abhängig vom
vorherigen Aufruf eines Linearverlaufs scheitern. Die gespeicherten SVGs
behalten ihren nativen Radialverlauf; die konzentrischen Renderhilfen
erscheinen ausschließlich im privaten Renderer-Eingang.

Nachgewiesen sind isolierte, annähernd kreisrunde Motive auf weißem
Hintergrund mit zentriertem radialem Verlauf. Dezentrale Reflexe, beliebige
Hintergründe und weitere Objekte sind nicht nachgewiesen. Die Restabweichung
der kleinen JPEGs bleibt in den Metriken sichtbar.

## Harte Abnahme am gespeicherten CLI-SVG

Ziel und fünf Farb-Holdouts werden unter fremden Dateinamen verarbeitet.
Die bisherigen XML-Beschreibungen bleiben im versiegelten Vorlauf erhalten.
Für `GE0285`, das keinen XML-Eintrag besitzt, verwendet auch der Vorlauf
die neutrale Beschreibung. Der Nachlauf erhält dieselbe eigenständige
Beschreibung in allen sechs Fällen.

| Variante | mean_delta2 vorher | mean_delta2 nachher | Edge-Alignment | Masken-IoU |
|---|---:|---:|---:|---:|
| GE0280 | 5009.374023 | 459.058960 | 0.846646 | 0.924051 |
| GE0281 | 14981.222656 | 308.333344 | 0.856544 | 0.972393 |
| GE0282 | 2103.857178 | 149.666672 | 0.896276 | 0.960938 |
| GE0283 | 7999.696289 | 527.800476 | 0.791777 | 0.936709 |
| GE0284 | 5833.063477 | 587.102051 | 0.826465 | 0.921136 |
| GE0285 | 4717.562500 | 516.340027 | 0.877270 | 0.986842 |

Alle sechs Fälle bestehen beide unveränderten Qualitätsgates.
Jede Pflichtmetrik verbessert sich oder bleibt unverändert gegenüber dem
kontrollierten Vorlauf. Der unabhängige Semantikcheck verlangt weißen
Hintergrund, genau einen Kreis und einen zentrierten nativen Radialverlauf
mit heller Mitte. Falsche Verlaufstypen, dezentrale Verläufe, zusätzliche
Formen, Transformationen und eingebettete Raster werden abgelehnt.
Ein identisch gerendertes PNG/SVG-Paar kalibriert alle Pflichtmetriken auf
die Idealwerte.

## Generalisierung und Reproduktion

Vier synthetische SVG→Raster→SVG-Roundtrips prüfen zwei zusätzliche Farben,
verschobene Lage und zwei Größen bis zum Doppelmaßstab. Die Beschreibung
enthält keine Geometriezahlen. Ein Runtime-Test verbietet Sample-SVG-Zugriff
und Raster-Embedding und verlangt identische SVG-Bytes nach Umbenennung.
Negativtests sichern fehlende Radialstruktur, zusätzliche Objekte,
widersprüchliche Beschreibungen, Renderausfall sowie nicht endliche und
nicht verbesserte Fehler.

`artifacts/evaluation/radial_disk_recheck_v1/` enthält Manifest mit
Quellhashes und Toolchain, versiegelte Baseline, zwölf eingefrorene
CLI-SVGs, CLI-Logs, Gatebericht und Reproduktionsbeleg. Zwei unabhängige
CLI-Läufe mit der finalen Implementierung reproduzieren sämtliche zwölf
SVG-Bytes und alle Gateentscheidungen.

```bash
python -m tools.run_radial_disk_recheck \
  artifacts/evaluation/radial_disk_recheck_v1/manifest.json \
  --output-dir .tmp/radial-disk-reproduction
python -m tools.evaluate_radial_disk_recheck \
  artifacts/evaluation/radial_disk_recheck_v1/manifest.json \
  --output .tmp/radial-disk-gates.json
python -m compileall src tests tools
python -m pytest -q
python -m src.imageCompositeConverter --help
python -m tools.check_no_new_image_id_hardcoding
```

Die 76 fokussierten Disk-/Pfeil-/Renderer-Tests sind grün. Einschließlich
der vier Unterprozess-Umgebungstests sind 80 Tests grün. Der vollständige
Abschlusslauf wird separat unter `completion_2026-10-06.json` protokolliert.
Syntaxprüfung, CLI-Help-Smoke und Runtime-ID-Nullprüfung sind grün
(`0 occurrences`). Die isolierte Umgebung verwendet CPython 3.12.14,
NumPy 2.5.3, OpenCV 4.14.0 und PyMuPDF 1.26.7. Zwei anfängliche
Unterprozessfehler im Gesamttest stammen aus dem bestehenden Linux-Pfadtrenner
im Windows-PYTHONPATH. Ein temporärer Bootstrap mit separat erhaltenem
Windows-Pfadeintrag lädt die passenden Bibliotheken vor der historischen
Vendor-/Virtualenv-Auswahl.

Anschließende Prüfungen machten drei bestehende Referenztests für
`AC0733_1_L`, `AC0701_1_S` und `AC0150_2` rot, weil parallel neu erzeugte Batch-SVGs
gegen feste Werte aus der versionierten Bestenliste geprüft wurden.
Diese Tests verwenden jetzt den bereits vorhandenen Bestenlisten-Snapshot
wie die anderen Snapshot-Tests. Erwartete Fehlerwerte, Topologieprüfungen
und Qualitätsgrenzen bleiben unverändert. Die 32 Review-Tests sind grün.

## Nächste Rotation

Der Review-Snapshot enthält 806 Einträge mit 802 renderbaren Paaren;
vier bereits fehlende SVG-Paare bleiben markiert. Die sechs belegten
Disk-Passes und alle zuvor separat belegten Pässe sind ausgeschlossen,
weil die historische Sammelausgabe weiterhin alte SVGs enthält. Der Aufruf
steht in `review_reproduction_2026-10-06.json`; die neuen Kandidaten beginnen
mit **GE9013_6M**, gefolgt von GE0300, GE1420_S, AC0403_1_L und AC0130_S.
Vor der Nachzeichnung ist jeweils eine frische CLI-Baseline zu prüfen.
Parallel laufende Katalogänderungen können den nächsten Review-Snapshot
verändern; die isolierte Disk-Abnahme bleibt über ihre Quellhashes überprüfbar.
