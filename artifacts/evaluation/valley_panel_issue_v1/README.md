# Nach unten gerichtete V-Linie: Issues #1909 und #1999

`AC0552_2_L.svg` und die drei zugehörigen Katalog-JPEGs zeigen ein grünes
Verlaufsrechteck mit dünnem grauem Rahmen und einer weißen offenen V-Linie.
Die bisherige Beschreibung „Wie AC0551: Wie AC0150“ nennt diese Formen nicht
eigenständig. Der bisherige allgemeine Panelfit zeichnet das Rechteck und lässt
die V-Linie weg. Der vorhandene Dachlinien-Fit unterstützt nur die Spitze oben.

Die grünen Größen L/M/S haben jetzt einen eigenen Katalogeintrag. Andere Farben
und Familien behalten ihre Beschreibungen. Quelle und Qualitätsgrenzen bleiben
unverändert. Die bereits vor diesem Paket korrigierte Inline-Stilpriorität
erzeugt ein anderes Prüfraster als die historischen Issues; deren Hashes und
Messwerte sind deshalb ausdrücklich historische Evidenz in `manifest.json`.

## Zwei überprüfte Lösungshypothesen

1. **Eigenständige Beschreibung allein:** Am Ausgangsstand `d2f110bd1` scheitert
   das Original weiterhin mit RGB-MSE 0,018558. Die Linie fehlt; der reguläre
   Runner stoppt nach 0/1 und startet keine Varianten. Derselbe Fehler tritt
   mit der historischen Beschreibung auf. Der exakte Vorherlauf wurde vor dem
   Restore der neuen Moduldatei über die echte isolierte CLI ausgeführt.
2. **Beschriebenes natives V aus dem Raster:** Der bestehende Dachlinien-Fit
   arbeitet für die neue Richtung mit gespiegelten Arbeitskoordinaten und
   schreibt unmittelbar native Rechteck-/Polylinien-/Verlaufskoordinaten.
   Es gibt weder Rastereinbettung noch kopierte Referenzvektoren oder einen
   neuen, quellennamengebundenen Algorithmus. Das Original besteht danach mit
   RGB-MSE 0,000100, Kontur 0,858706 und IoU 0,998187.

Der erste native Versuch scheitert noch bei beschnittenen Varianten. Sichtbare
neutrale Pixel an allen vier Randbändern begrenzen jetzt die graue Rahmenfarbe.
Wenn sämtliche Seiten außerhalb des Ausschnitts liegen, darf der Rahmen nur
außerhalb des sichtbaren Viewports starten. Die Verlaufslage bleibt unabhängig
von der Rahmensuche im Bildkoordinatensystem. Beim kleinsten JPEG verfehlt die
gleichmäßige Stoppauswahl eine beobachtete Steigungsänderung; die zusätzliche
adaptive Hypothese bleibt ebenfalls auf neun kontinuierliche Stopps begrenzt.

Absolute und quadratische Verluste sowie unabhängige Rechteckseiten liefern
begrenzte Alternativen nach verfehlten Gates. Hypothesen, Fehler, tatsächliche
Renderzahlen und gewählte Parameter stehen im Produktions-Checkpoint und in
`checks.json`. Höchstens 1.800 verschiedene Kandidatenrenderings sind erlaubt;
die 51 Seedfälle benötigen höchstens 295, die neun zusätzlichen Fälle höchstens
1.182. Das gemeinsame Bildbudget gilt weiter. Ungeklärte kompakte helle/dunkle
Innenobjekte, falsche Farben/Richtung/Achse und unvollständig verbrauchte
Beschreibungen verhindern die Freigabe dieses Modells.

## Abnahme

| Prüfung mit 64 Iterationen / 60 Sekunden je Fall | Ergebnis |
| --- | --- |
| #1909, vollständiger Seed 2820021284389229367 | 17/17 |
| #1999, vollständiger Seed 7262616060025015007 | 17/17 |
| Neuer Seed 817263 | 17/17 |
| Unabhängige grüne/blaue/rote Panels, zwei Größen, asymmetrische Schenkel | 6/6 |
| Katalog-JPEGs L/M/S unter fremden Dateinamen | 3/3 |

Der eigenständige Nachprüfer liest die gespeicherten SVGs und Eingaberaster.
Er prüft Richtung, beide Schenkel, Anschluss an die Seiten, Farbe, native
Elemente, Stopplimit, fehlende Zusatzformen/Transformationen, Eingabe-/Ausgabehashes,
unveränderte Pixelgates, Renderzahlen und Laufzeit. Referenz-SVG-Zugriffe der
CLI bleiben gesperrt. Die Erfolgsarchivzahl wird hierdurch nicht erhöht.

Die lokalen Regressionen bestehen: 236 gezielte Tests, anschließend die finale
V-Linien-Suite mit 26 Tests einschließlich zusätzlicher Negativkontrollen und
42 Kernprüfungen. Diese Testmengen überlappen. Die GitHub-CI wiederholt beide
Issue-Seeds, den Zusatzseed und alle neun unabhängigen Fälle und bewahrt die
Rohdaten 14 Tage. Die Issues werden erst mit Übernahme des PRs geschlossen.

## Wiederholung

Ausgabeordner müssen neu sein. `manifest.json` prüft SVG-/Beschreibungshashes
vor dem ersten Aufruf; Python erhält die vollständigen Integer-Seeds.

```powershell
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --manifest artifacts/evaluation/valley_panel_issue_v1/manifest.json --output-dir .tmp/valley-frozen
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --manifest artifacts/evaluation/valley_panel_issue_v1/manifest.json --output-dir .tmp/valley-holdout --issues 1909 --seed 817263
.venv/Scripts/python.exe -m tools.evaluate_valley_panel --output-dir .tmp/valley-independent
.venv/Scripts/python.exe -m tools.verify_valley_panel_acceptance --run .tmp/valley-frozen/1909 --run .tmp/valley-frozen/1999 --run .tmp/valley-holdout/1909 --independent .tmp/valley-independent
.venv/Scripts/python.exe -m pytest -q tests/test_valley_panel_runtime.py tests/test_chevron_panel_runtime.py tests/test_plan_b_issue_inventory.py tests/detailtests/test_plan_b_variations.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py
.venv/Scripts/python.exe tools/run_pytest_profile.py core-green
```

`summary.json` bezeichnet die gültigen lokalen Vorher-/Nachherverzeichnisse
und erhält auch den erfolglosen ersten nativen Versuch. Rohbilder, SVGs und
CLI-Logs bleiben dort; nur kompakte Nachweise werden eingecheckt.
