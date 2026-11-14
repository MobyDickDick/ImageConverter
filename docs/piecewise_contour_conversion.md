# Mehrstufige Freiform-Konvertierung mit ausgerichteten Rastervarianten

Der neue Suchweg rekonstruiert einen Verlaufskreis und eine zweifarbige Freiform
mit Kontur. Er ist in den normalen Converter eingebunden. Die Konturzerlegung
ist unabhängig vom Motiv; die Szenenerkennung unterstützt zunächst diese
begrenzte Kombination. Es werden keine gespeicherten SVGs, Katalogkoordinaten
oder Handvorlagen als Rekonstruktionshilfe gelesen.

## Algorithmus

1. **Hintergrund separat rekonstruieren.** Aus dem sichtbaren Kreisrand werden
   Mittelpunkt und Radius geschätzt. Ein robuster Ebenenfit findet sichtbare
   Verlaufspixel trotz davorliegender Freiform. Eine Rang-1-Näherung bestimmt
   die Verlaufsrichtung aus beiden Bildachsen. Kreis, grauer Rand, Endfarben
   und Richtung werden am Raster nachoptimiert. Dieser Zwischenschritt besitzt
   ein eigenes begrenztes Suchprogramm; eine fehlende Vordergrundform löst
   keine unbeschränkte Suche nach einem vollständigen Bild aus.
2. **Vordergrund extrahieren.** Zwei am Original geschätzte Farbwerte beschreiben
   Kontur und Innenfläche. Farbmatting gegen den rekonstruierten Hintergrund
   liefert weiche Masken für die äussere Silhouette und die Füllung. Die dunkle
   Silhouette liegt unter der hellen Innenfläche; dadurch bleiben auch innere
   Trennlinien und die Öffnung zwischen den Fingern darstellbar.
3. **Weitere Raster ausrichten.** Für eine Datei mit Grössensuffix `_L`, `_M`
   oder `_S` werden nur die beiden exakten Geschwister desselben Dateistamms
   geladen. Nummerierte und andersfarbige Varianten bleiben getrennt. Zunächst
   wird auf die Zielgrösse gezoomt, danach bestimmt ECC eine affine Korrektur
   einschliesslich Translation und kleiner Skalierungsänderungen. Zu starke
   Verformung, ungenügende Korrelation oder abweichende Farben führen zur
   Zurückweisung. Zoomfaktoren und Transformationsmatrizen werden protokolliert.
4. **Lokale Teilkonvertierungen.** Subpixel-Isolinien der Masken werden in
   kurze Konturabschnitte geteilt. Jeder Abschnitt erhält einen eigenen
   kubischen Bézier-Fit mit kleinster Quadrate. Passt er nicht innerhalb der
   Toleranz, wird er am Fehlermaximum weiter unterteilt und erneut angepasst.
   Die Teile sind Kurvenstücke; es gibt keine vorausgesetzte anatomische
   Erkennung von Fingern oder Handfläche.
5. **Glatt zusammensetzen.** Alle Abschnitte verwenden gemeinsame Endpunkte
   und Tangenten. Dadurch stimmen die Anschlüsse exakt überein und sind
   tangential glatt (G1), auch beim Schliessen eines Pfades. Unterschiedliche
   Griffweiten erlauben unterschiedliche Kurvenlängen. Pro Farbe entsteht ein
   zusammengesetzter Pfad mit `fill-rule="evenodd"`; Öffnungen werden als
   Teilpfade erhalten. Künstliche Teilgrenzen werden nicht gezeichnet.
   Es ist deshalb keine fehleranfällige nachträgliche Vereinigung unabhängig
   gerasterter Kacheln erforderlich.
6. **Wiederholen und prüfen.** Toleranzen 0,65 / 0,40 / 0,25 / 0,16 Pixel
   liefern zunehmend feinere Kandidaten. Einzelbild und ausgerichtete
   Überlagerung werden beide geprüft. Die Überlagerung verwendet 60 Prozent
   Originalmaske und 40 Prozent Median der ausgerichteten Begleiter. Sie darf
   die Topologie des Originals nicht ändern. Übernommen wird nur ein Kandidat,
   der die lokalen und globalen Prüfungen besteht und den bisherigen Fehler
   verbessert. Ein Begleitbild erzwingt somit keine Änderung eines guten Fits.

Die lokale Prüfung fordert mindestens 0,92 Masken-IoU für Silhouette und Füllung,
gleiche Anzahl bedeutender Komponenten/Öffnungen und einen normierten Fehler
von höchstens 0,012 in jedem betroffenen 6×6-Bereich. Die bestehenden globalen
Grenzen bleiben unverändert. Die Suche endet spätestens am Bildzeitlimit oder
am Kurvenbudget von 160 SVG-Pfadbefehlen. Auch ein späteres allgemeines
SVG-Polieren muss Objektbestand und lokale Maskentopologie erneut bestehen,
bevor es das Ergebnis ersetzen und eine Abnahme erhalten darf.

## Verwendung und Schnittstellen

Für das Beispiel genügt die normale CLI:

```powershell
.venv/Scripts/python.exe -m tools.convert_one_image GE0023_1_L --output-dir .tmp/piecewise
```

Die beiden XML-Beschreibungstabellen enthalten jetzt eigene Beschreibungen für
die sechs Handbilder. Die gemeinsame Familienbeschreibung nennt einen Pfeil
und bleibt für das tatsächlich pfeilförmige `GE0023.jpg` erhalten.

Eine allgemeine, bewusst eindeutige Szenenbeschreibung lautet:

> Im Hintergrund liegt ein Kreis mit grauem Rand und einem farbigen Farbverlauf.
> Davor liegt eine farbige Freiform mit dunkler Kontur. Die Vordergrundform kann
> Öffnungen und schmale Ausläufer besitzen. Keine Beschriftung oder weiteren Zeichen.

`fit_paint_boundary(alpha, tolerance=..., max_segments=..., cancelled=...)`
in `imageCompositeConverterPiecewiseContours.py` kann unabhängig von dieser
Szenenbeschreibung beliebige weiche Flächenmasken vektorisieren.
`fit_piecewise_scene(..., companion_images=[(name, bgr_array), ...])` nimmt bis
zu vier zusätzliche Raster entgegen. Die Runtime sucht Grössengeschwister
automatisch; die Funktion selbst liest keine Dateien.

Vergleich, Kurvenabschnitte, Ausrichtungsbelege und beide Rendererprüfungen:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_piecewise_scene artifacts/images_to_convert/GE0023_1_L.jpg artifacts/images_to_convert/GE0023_1_M.jpg artifacts/images_to_convert/GE0023_1_S.jpg --output .tmp/piecewise-review
.venv/Scripts/python.exe -m pytest tests/test_piecewise_contours.py -q
```

## Grenzen

Die Zerlegung rekonstruiert beobachtete Rasterkonturen. Sie ersetzt keine
semantische Handerkennung und kann verlorene Details eines kleinen JPEGs nicht
zuverlässig erfinden. Die Einbindung unterstützt einen ausreichend sichtbaren
Kreis, einen annähernd linearen Farbverlauf und zwei unterscheidbare
Vordergrundfarben. Vordergrund am Kreisrand, Text, weitere Objekte, beliebige
Schattierungen und widersprüchliche Beschreibungen benötigen zusätzliche
Modelle. Zeit-/Kurvenbudget oder eine fehlgeschlagene lokale Prüfung liefern
keine Abnahme.

Bei den drei hautfarbenen Handbildern bestehen beide Renderer. Der Verlauf
liegt nahezu vertikal. Die zusätzliche Überlagerung verbessert S geringfügig;
bei L und M bleibt der Einzelbild-Fit besser. Von den drei zusätzlich
untersuchten grauen Varianten bestehen L und M. S wird wegen einer nicht
stabil rekonstruierten Füllungsöffnung zurückgewiesen. Ein guter globaler
Pixelwert allein hebt diese Zurückweisung nicht auf.
