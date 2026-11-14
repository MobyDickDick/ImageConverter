# AC0022: Dreieckköpfe und horizontale Querlinie

Der echte CLI-Lauf verwendet die unveränderten JPEG-Bytes von
`artifacts/images_to_convert/AC0022.jpg` unter dem neutralen Namen `NEUTRAL.jpg`
und die ursprüngliche Benutzereingabe einschließlich „untten“ und Kommas.
Die Beschreibung steht vollständig in `summary.json`.

Die begrenzte Normalisierung korrigiert wiederholte Buchstaben in
„Spitze nach oben/unten“, ohne zitierte Beschriftungen zu ändern. Kommas
trennen die Richtungsangabe nicht mehr von der zugehörigen Seite.
Widersprüchliche Seitenfarben und Richtungen werden weiterhin zurückgewiesen.

Der Beschreibungskontrakt dieses Pfeilpaars verlangt zwei native,
nicht degenerierte Dreiecke. Die ausdrücklich rote horizontale Linie muss
als waagerechte native Linie oder schmales Rechteck nachgewiesen werden.
Die Prüfung greift vor Ersatzvorschlägen, vor dem Speichern und vor
validierten Zwischenständen. Sie zertifiziert keine beliebigen SVG-Pfade
oder gedrehten Gruppen als horizontale Linie.

Ergebnis: echter CLI-Lauf **1/1 validiert**, kein SVG-Referenzzugriff,
unveränderte Pixel-/Komplexitätsgrenzen mit **MuPDF und librsvg bestanden**.
Der vorherige pixelakzeptierte Kreisentwurf wird mit
`object_count:triangle:2:1` abgelehnt. Die neue Querlinie ist exakt horizontal;
ihre Höhe wird weiterhin am Raster angepasst.

Lokale Ausgabe: `conversion/converted_svgs/NEUTRAL.svg`,
vierfach vergrößerte unabhängige Vorschau: `result.png`.
Große Laufartefakte bleiben gemäß Repository-Regeln lokal.

Gezielte Tests:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_arrow_pair_runtime.py tests/test_description_language.py tests/detailtests/test_dual_arrow_runtime_helpers.py tests/test_fallback_structure.py tests/test_fallback_groups.py tests/test_fallback_composition.py
```

Die Gegenproben umfassen Kreise/Ellipsen statt Dreiecken, degenerierte
Polygone, Dreiecke nur in Definitionen sowie schräge, blaue oder gedrehte
Querlinien. Farb-/Richtungskonflikte, übersetzte Varianten und bestehende
Fallback-Kompositionen bleiben geprüft.
