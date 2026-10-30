# Helligkeitsverlauf im gerahmten Panel, 30. Oktober 2026

Der erhaltene GUI-Auftrag für `AC0VR2_M.jpg` reproduziert die Beanstandung:
2,7 Sekunden Laufzeit, keine zusätzlichen Kandidaten und eine bestandene
globale Pixelprüfung trotz eines deutlich zu dunklen Glanzbands. Die bisherige
Näherung verwendet die Medianfarbe eines grossen Innenbereichs als hellste
Verlaufsfarbe und mittelt auch die dunklen Endbereiche zu stark.

Der native Registrierungsweg `imageCompositeConverterFramedPanel` passt vier
Farbstopps mit zwei freien inneren Positionen an das gemessene Profil an.
Anschliessend verfeinert die gemeinsame Registrierung Farben, Positionen,
Rechteckgrenzen und Konturbreite. Die Modellgrösse bleibt unabhängig von der
Rasterauflösung: ein Rechteck und ein kontinuierlicher SVG-Verlauf, ohne
Rastereinbettung oder nachgezeichnete Zeilen. Auswahl und Anpassung verwenden
die Beschreibung und Rasterpixel, keine Dateinamen oder Referenz-SVGs.

Zusätzlich zu den unveränderten globalen Pixelgrenzen muss das lokale Profil
passen: höchstens vier Graustufen Abweichung am 95. Perzentil und höchstens
drei beim hellsten Bereich. Der bisherige Kandidat verfehlt beide Grenzen
mit 17 Graustufen. Zusätzliche Formen, Farbe, fehlender Glanz und ein entgegen
der Beschreibung umgekehrter Verlauf werden vom Modell abgelehnt.

Ein neuer Auftrag über dieselbe `Jobs`-Implementierung wie die GUI benötigt
5,1 Sekunden und prüft 178 Kandidaten. Er endet mit `satisfactory=true`.
Der mittlere quadratische Pixelfehler sinkt von 100,0122 auf 1,9911,
der Profilfehler von 17 auf 2 und der Spitzenfehler von 17 auf 1 Graustufe.
Die unabhängige Darstellung mit librsvg (`rsvg-convert`) bestätigt das Ergebnis
mit MSE 1,9989 und denselben lokalen Profilwerten. Es gibt keine künstliche
Mindestlaufzeit; das Suchbudget bleibt eine Obergrenze.

Reproduzierbare Tests stehen in `tests/test_framed_panel_runtime.py`:
Original-JPEG, neutral benannter CLI-/GUI-Export mit frischer Beschreibung,
sechs unabhängige Fälle mit anderen Auflösungen, Abständen, Konturbreiten,
Verlaufslagen und Achsen sowie negative Modell-/Renderer-/Budgetkontrollen.
Die neutral benannte CLI-Prüfung verwendet dieselben isolierten, wiederverwendeten
Renderworker-Einstellungen wie die GUI.

Validierung: 141/141 Tests für gerahmte, axiale und markierte Panels sowie
die betroffenen Laufzeit-/Verlaufshilfen; zusätzlich 25/25 GUI-Tests.
Die zwei GUI-Tests für lokale HTTP-Verbindungen und Prozessabbruch bestehen
ausserhalb der Sandbox, deren Rechte diese Operationen sonst blockieren.

Die Messwerte bleiben in `summary.json`. Das korrigierte `AC0VR2_M.svg`,
der unabhängige Prüfraster und `comparison.png` liegen lokal in diesem Ordner;
die bisherigen GUI-Ergebnisse bleiben erhalten.
