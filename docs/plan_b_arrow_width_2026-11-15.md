# Plan-B: gemeinsame Linienbreite bei Pfeilpaaren

Die Workbench-Aufgabe `b231e7854c0041b1916eff717851a2dd` für `AC0090_L.svg`
scheiterte im ersten Versuch in allen 17 Fällen. Die Beschreibung verlangt
„Alle Linien sind gleich breit“. Jeder Konverterprozess meldete
`DescriptionRejected: unequal_line_widths`; anschließend enthielt seine
Fehlerausgabe nur ein eingebettetes Rasterbild. Deshalb waren die Pixelwerte
perfekt, die Plan-B-Befunde aber `embedded_raster` und `no_vectors`.

Zwei Ursachen wurden geprüft: ungleiche Breiten bereits in der Referenz oder
unabhängige Breiten bei der Rekonstruktion. Die drei Linien des Original-SVGs
sind jeweils `1.511312` breit. Auch alle 16 transformierten Referenzen bestehen
die Prüfung der tatsächlich dargestellten Breiten. Der neue Regressionstest
scheitert dagegen mit dem alten Konverter schon beim Rendern seines ersten
unabhängig geschätzten Kandidaten mit `unequal_line_widths`.

Der Pfeilfitter verwendet bei einer positiven Gleichheitsbedingung jetzt einen
einzigen optimierbaren Breitenparameter für beide Schäfte und den optionalen
Querstrich. Der Startwert ist der Median der aus dem Raster beobachteten Breiten;
keine numerische Breite stammt aus der SVG-Referenz oder dem Dateinamen. Die
Position des Querstrichs wird dabei über seine Mitte gesucht, damit eine
Breitenänderung ihn nicht verschiebt. Ohne positive Gleichheitsbedingung bleiben
die Breiten unabhängig.

Die Bindung gilt bereits für jeden Suchkandidaten, vor Rasterisierung und
Fehlerberechnung. Eine bloße Änderung des fertigen SVGs würde dessen bisherige
Rasterbewertung ungültig machen. Qualitätsgrenzen und abschließende
Beschreibungsprüfung bleiben unverändert.

## Nachweis

Der gemeinsame zweite Versuch derselben GUI-Aufgabe besteht **17/17 Fälle**.
Der erste Versuch bleibt erhalten. Eingabehashes, vollständige Beschreibungen,
Seed `229378669285018661`, 64 Iterationen und 60 Sekunden je Fall sind identisch:

```powershell
.venv/Scripts/python.exe -m tools.plan_b_workbench --run-dir artifacts/gui/workbench/b231e7854c0041b1916eff717851a2dd --cases all --iterations 64 --timeout-seconds 60
```

Alle gespeicherten Ausgaben bestehen zusätzlich die Beschreibungs- und
Breitenprüfung, enthalten genau drei Rechtecke und zwei Dreiecke und weisen
keine verbotenen SVG-Zugriffe auf. Die unabhängige erneute Rasterbewertung aller
17 gespeicherten SVGs reproduziert die Berichtswerte. Höchste normierte MSE:
`0.00026060` bei erlaubten `0.01`; kleinste Kantenübereinstimmung: `0.98323` bei
geforderten `0.72`; kleinste Vordergrundüberdeckung: `0.99874` bei geforderten
`0.85`. Die Summe der Falllaufzeiten beträgt vorher `48.673`, nachher `64.763`
Sekunden; parallel laufende Regressionstests verhindern einen isolierten
Laufzeitvergleich.

Die neuen Regressionstests verwenden unabhängig erzeugte Pfeilpaare mit und
ohne Querstrich, anderen Farben und verschobenen Positionen. Sie prüfen die
Breitengleichheit bei jedem gerenderten Suchkandidaten, die tatsächliche Suche
über verschiedene gemeinsame Breiten und die Übereinstimmung von Ausgabe-SVG
und bewertetem Raster. Gegenproben erhalten unterschiedliche Schaftbreiten bei
fehlender oder negierter Gleichheitsbedingung. Die bisherigen Tests prüfen
außerdem widersprüchliche Farben und Pfeilrichtungen sowie fehlende und
zusätzliche Objekte.

164 gezielte Tests bestehen:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_arrow_pair_runtime.py tests/test_arrow_pair_conditions.py tests/test_stroke_constraints.py tests/detailtests/test_dual_arrow_runtime_helpers.py -q
```

Einzelmesswerte, Hashes, Renderzahlen und Softwarefingerabdruck stehen in
`artifacts/evaluation/arrow_pair_shared_width_2026-11-15/summary.json`.
Die aktualisierte GUI-Aufgabe zeigt die Ergebnisse nach dem Neuladen.
