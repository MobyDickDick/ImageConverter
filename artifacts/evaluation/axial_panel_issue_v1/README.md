# Referenz, Beschreibung und Konvertierungsqualität für Issue #1980

Der schwarze Streifen war keine verlässliche Referenz für `z_201.svg`.
Die allgemeine Renderkette löste Inline-Stile ohne `<style>`-Block nicht auf;
die lokalen `href`-/`xlink:href`-Verweise auf die Verlaufsstopps fehlten im
privaten MuPDF-Eingabedokument. Beide Ursachen sind korrigiert. Das Quell-SVG
bleibt bytegleich, und gespeicherte Konvertierungen bleiben native Vektoren.
Externe oder zyklische Verlaufsverweise werden nicht verfolgt.

## Unabhängige Quellenprüfung

sharp 0.35.5 / librsvg 2.63.2 zeichnet dasselbe rosa Rechteck mit heller oberer
Zone, dunklerer unterer Zone und kräftigerem rosa Abschluss. Original und
16 Transformationen werden in 51 × 5 und 510 × 50 Pixeln verglichen. Beide
Renderer erhalten denselben expliziten Pixel-Viewport; Inhalt, `viewBox`,
Stile und Transformationen bleiben erhalten. Alle 34 Vergleiche bestehen die
separate Renderer-Toleranz von RGB-MSE < 0,001; maximal gemessen: 0,000181.
Das ist keine Änderung der Konvertierungsgrenzen. Neue analytische Kontrollen
prüfen andere Namen, Farben, verschachtelte Referenzen, Achsenumkehr und
Transformationen. Die Originalbytes und alle Vergleichsraster bleiben lokal
unter `.tmp/issue-1980-reference-audit/`; `checks.json` enthält ihre Messwerte.

## Beschreibung und neue Baseline

Der Katalog führt das Bild als eigenen Eintrag statt unter der allgemeinen
Rohrbeschreibung. Er beschreibt ein einzelnes waagerechtes, sehr flaches
Rechteck ohne Kontur mit dem beobachteten vertikalen rosa Verlauf. Es gibt
keinen überschreibenden Sidecar. `select_task`, Katalog und `manifest.json`
verwenden dieselbe Beschreibung. Quelle, neue Beschreibungs-/Rasterhashes,
vollständiger Originalseed und Budget bleiben gespeichert.

Nach Renderer- und Beschreibungskorrektur, vor dem neuen Konvertierungsmodell,
scheitert das Original mit RGB-MSE 0,014599, Kontur 0,345729 und IoU 0,337580.
Der reguläre Runner stoppt deshalb nach 0/1 und startet keine Varianten.
Dieser neue Ausgangslauf ist ausdrücklich von den historischen 3/17- und
2/17-Ergebnissen der schwarzen Referenz getrennt. Vollständiger lokaler Beleg:
`.tmp/issue-1980-corrected-baseline/`.

## Zwei begrenzte Modellhypothesen

Der neue allgemeine Suchweg benötigt eine eigenständige Beschreibung eines
einzelnen konturlosen Rechtecks mit axialem Farbverlauf. Lage, Größe, Farbe
und Richtung kommen aus Raster und Beschreibung. Orthogonale Bildstruktur,
Zusatzobjekte, falsche Farben und unverbrauchte Beschreibungsaussagen lehnen
das Modell ab. Die beschriebenen rosa Zonen werden an Ein- und Ausgabe geprüft.

Zuerst wird ein kontinuierlicher Verlauf mit zwei Endfarben gemessen. Für das
Original besteht dieser Kandidat die Abnahme nicht (Aufruferfehler 7,326797).
Die Alternative passt höchstens vier kontinuierliche Stopps mit zwei freien
inneren Positionen an; sie besteht mit Aufruferfehler 0,270588. Die Modellgröße
hängt nicht von der Pixelzahl ab. Es entstehen weder Rasterstreifen noch
nachgezeichnete Konturen. Höchstens fünf echte Kandidatenrenderings sind erlaubt;
die 34 Quellenfälle benötigen jeweils zwei bis vier. Das gemeinsame Bildbudget bleibt
verbindlich. Hypothesen, Parameter und tatsächliche Prüfzahlen stehen im
Produktions-Checkpoint und in `summary.json`.

| Abnahme mit 64 Iterationen und 60 Sekunden je Fall | Ergebnis |
| --- | --- |
| Originalseed 347146220485913939 | 17/17 |
| Zusatzseed 817263 | 17/17 |
| Unabhängige blaue/graue Rechtecke, zwei Größen und beide Achsen | 8/8 |

Alle Aufrufe verwenden die echte CLI, unveränderte Qualitäts-/Komplexitätsgates
und gesperrte Referenz-SVG-Zugriffe. Der unabhängige Nachprüfer liest die
gespeicherten SVGs und prüft ein natives Rechteck, höchstens vier Stopps,
fehlende Raster/Schrift/Zusatzformen, Lage, rosa Zonen und tatsächliche Budgets.
Negativkontrollen betreffen falsche Farbe/Achse, flache Füllung, Zusatzmarke,
geteilte Fläche, widersprüchliche Sprache, fehlende Verlaufszonen und Timeout.
Die Erfolgsarchivzahl bleibt unverändert. Das Issue wird erst beim Merge des
Korrektur-PRs geschlossen; die historische Evidenz bleibt erhalten.

Lokale Regression: 185 gezielte Tests, 267 breitere Verlaufssymbol-/Renderprüfungen
und 42 Kernprüfungen bestehen. Die vollständige GitHub-CI ist ein separater
Nachweis am Pull Request.

## Wiederholung

Alle Ausgabeordner müssen neu sein. Die CI bewahrt Rohdaten 14 Tage und prüft
beide Seeds, den unabhängigen Renderer und die acht zusätzlichen CLI-Fälle.

```powershell
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --manifest artifacts/evaluation/axial_panel_issue_v1/manifest.json --output-dir .tmp/panel-frozen
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --manifest artifacts/evaluation/axial_panel_issue_v1/manifest.json --output-dir .tmp/panel-holdout --seed 817263
.venv/Scripts/python.exe -m tools.evaluate_axial_panel --output-dir .tmp/panel-independent
.venv/Scripts/python.exe -m tools.verify_axial_panel_acceptance --run .tmp/panel-frozen/1980 --run .tmp/panel-holdout/1980 --independent .tmp/panel-independent
.venv/Scripts/python.exe -m pytest -q tests/test_axial_panel_runtime.py tests/detailtests/test_svg_gradient_references.py tests/detailtests/test_rendering_gradient_compatibility.py tests/detailtests/test_plan_b_variations.py
.venv/Scripts/python.exe tools/run_pytest_profile.py core-green
```

Für die unabhängige Rendererprüfung nimmt `tools.audit_plan_b_svg_reference`
zusätzlich `--node`, `--sharp-module` und eine UTF-8-Beschreibungsdatei entgegen.
Die CI zeigt den vollständigen Aufruf mit der separat installierten
Audit-Abhängigkeit. Diese ist keine neue Produktionsabhängigkeit.
