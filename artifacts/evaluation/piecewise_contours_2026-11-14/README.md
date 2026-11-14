# Mehrstufige Hand-/Freiform-Konvertierung

Die neue Runtime zerlegt weiche Konturmasken in lokal gefittete BÃ©zier-Abschnitte
und setzt sie mit gemeinsamen Endpunkten und Tangenten zusammen. Die
[Algorithmusbeschreibung](../../../docs/piecewise_contour_conversion.md)
nennt Schnittstellen, Grenzen und Reproduktionsbefehle.

## Ergebnisse

Die drei hautfarbenen Original-JPEGs `GE0023_1_L/M/S` bestehen die unverÃ¤nderten
Pixel-/Kanten-/KomplexitÃ¤tsgrenzen mit MuPDF und librsvg, zusÃ¤tzlich die neuen
lokalen Masken- und TopologieprÃ¼fungen. Die rekonstruierte Verlaufsrichtung liegt
bei etwa 90 Grad, also nahezu vertikal. Die Ausgabe besteht aus Kreis,
HintergrundflÃ¤che und zwei zusammengesetzten Vordergrundpfaden, ohne Bitmap.

Die weiteren GrÃ¶ssen werden zuerst gezoomt, danach mit einer affinen
ECC-Korrektur ausgerichtet. FÃ¼r L betrÃ¤gt der anfÃ¤ngliche Zoom von M 70/60 und
von S 70/50; die verbleibenden Verschiebungen liegen unter 0,1 Zielpixel.
Matrix, Korrelation und FarbenprÃ¼fung stehen pro Begleiter im Bericht.
Bei L und M bleibt die EinzelbildschÃ¤tzung besser. Bei S gewinnt die
Ãœberlagerung mit etwa 0,34 Prozent geringerem quadratischem Pixelfehler.
Das ist eine kleine Verbesserung, kein Nachweis zusÃ¤tzlicher verlorener Details.

Der normale CLI-Lauf fÃ¼r L erhÃ¤lt `status=validated`. Seine abschliessende
Vektorpolitur wird erneut auf lokale Maskentopologie und Objektbestand geprÃ¼ft.
Auch diese tatsÃ¤chlich gespeicherte CLI-Ausgabe besteht beide RendererprÃ¼fungen.

Die zusÃ¤tzliche graue Handfamilie ist ein explorativer Test: L und M bestehen;
S bleibt zurÃ¼ckgewiesen, weil eine Ã–ffnung der FÃ¼llungsmaske nach dem Rendern
nicht stabil erhalten bleibt. Die GesamtpixelprÃ¼fung wÃ¼rde dort allein bestehen.

## Lokale Artefakte

- `skin/<Bildstamm>/result.svg`: vollstÃ¤ndiges SVG.
- `skin/<Bildstamm>/background.svg`: separat rekonstruierter Hintergrund.
- `skin/<Bildstamm>/arcs.svg`: unterschiedlich gefÃ¤rbte Einzelabschnitte.
- `skin/<Bildstamm>/comparison.png`: Original, Hintergrund, ausgerichtete Kanten,
  Einzelabschnitte, zusammengesetztes Ergebnis und fÃ¼nffache Differenz.
- `skin/<Bildstamm>/report.json`: alle Verfeinerungsrunden, Transformationsmatrizen,
  MaskenprÃ¼fungen und unabhÃ¤ngige Renderermessungen.
- `cli_verified/`: echter Lauf der normalen CLI mit gespeicherten Berichten.
- `summary.json`: kompakter Abnahmenachweis mit QuellprÃ¼fsummen.

Rohartefakte bleiben gemÃ¤ss Repository-Regel lokal und sind reproduzierbar.
Das JPG und die historischen SVGs wurden beim Fit nicht verÃ¤ndert oder als
Referenzpfade gelesen. Die sechs spezifischen Handbeschreibungen ersetzen in
beiden Tabellen die unzutreffende geerbte Pfeilbeschreibung. Das Pfeilbild
`GE0023.jpg` bleibt bei seiner eigenen bisherigen Beschreibung.

## Tests

169 fokussierte Tests bestehen, darunter die neuen Konturtests, bestehende
Panel-/Kreis-/RÃ¶hrenmodelle und die Runtime-Einbindung. Nach der abschliessenden
Begrenzung des Supersampling-Speichers bestehen erneut alle zehn Konturtests.
Die neuen Tests verwenden unabhÃ¤ngig mit OpenCV erzeugte, unbekannte
Freiformraster mit Ã–ffnungen und schmalen AuslÃ¤ufern, unterschiedliche GrÃ¶ssen
und Verlaufswinkel sowie verschobene/verkleinerte Begleiter. Exakte AnschlÃ¼sse,
G1-Tangenten, Topologieverlust, Zusatzobjekte, Zeitlimit und Variantenisolation
werden gesondert geprÃ¼ft.

Der vollstÃ¤ndige Repository-Testlauf und die Katalogaktualisierung werden im
Abschlussnachweis ergÃ¤nzt. Ein separat reproduzierter Fehler der Gesamtsuite
betrifft den bereits unterschiedlichen Inhalt von
`artifacts/converted_images/converted_svgs/AC0VR2_ZL_M.svg` und
`tests/fixtures/plan_b_templates/AC0VR2_ZL_M.svg`; beide Dateien wurden durch
diese Arbeit nicht geÃ¤ndert.

Die Katalogübersicht wurde für alle 1.787 Bilder nachgeführt (3.095 neue
Paarmessungen, sechs wiederverwendete Messungen). Sie enthält die korrigierten
Handbeschreibungen. Die neuen Hand-SVGs liegen als lokale Versuchsartefakte
vor; historische Archivausgaben wurden nicht durch sie ersetzt.

Abschlussdaten: `checks.json`. Die übrigen Tests der Gesamtsuite
wurden nach dem beschriebenen Abbruch nicht vollständig ausgeführt.
