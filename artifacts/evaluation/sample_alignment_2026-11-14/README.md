# Sample gemeinsam skalieren: AC0030

Der hochgeladene Sample-Stand und die Originalpixel des gemeldeten GUI-Laufs
liegen für die Regression unter `tests/fixtures/sample_alignment`.

Der Sample-Pfad passt jetzt das gesamte vorhandene SVG gemeinsam an:
Skalierung, Verschiebung und gekoppelte Farben. Individuelle Pfadkoordinaten,
Polygonpunkte, Symbolgrößen und Deckkräfte werden nicht mehr einzeln verändert.
Bereits bestandene Samples bleiben unverändert. Bestehende dunkle Farbgruppen
dürfen beim Farbfit nicht im Hintergrund verschwinden.

Bei AC0030 beträgt die gefundene Skalierung auf beiden Achsen 0,896875,
die Verschiebung 0,5 Pixel nach rechts und 0,25 Pixel nach unten.
Das Minus, beide Diagonalen und der Rahmen behalten ihre ursprüngliche
Geometrie und werden gemeinsam transformiert. Der mittlere normalisierte
Pixelfehler sinkt von 0,01804654 auf 0,00060810 (96,6 Prozent).
Die unveränderten Pixelgrenzen bestehen mit MuPDF und librsvg.

`AC0030_corrected.svg` ist das tatsächliche Sample-Ergebnis;
`AC0030_corrected.json` enthält den vollständigen Messbericht.
`preview.png` zeigt das SVG mit librsvg in fünffacher Größe.

Validierung: 99 Tests bestanden, darunter der echte GUI-Sample-Lauf,
sechs unabhängige Skalierungs-/Verschiebungs-/JPEG-Fälle, Erhaltung aller
Originalgeometrien, bisherige Sample-Verträge und Ähnlichkeitsreferenzen.
`git diff --check` ist sauber.
