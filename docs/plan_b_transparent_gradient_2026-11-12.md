# Plan-B-Rasterfehler bei transparentem Verlauf, 12.11.2026

Das vom Nutzer bereitgestellte `plan-b-workbench.zip` enthält einen vollständigen
Diagnoselauf für `AC0VR2_AB_M.svg`, Seed `64217`, 64 Iterationen und 60 Sekunden
je Fall. Alle 17 bisherigen Ergebnisse scheitern an den Qualitätsgrenzen.

## Ursache und Korrektur

Der Hauptverlauf der unveränderten Quell-SVG ist bereits vertikal
(`x1=x2=0`, `y1=0`, `y2=30`). Eine zweite Rechteckfüllung legt einen schwachen
horizontalen Glanz mit `stop-opacity=0.16` bis `0.18` darüber.

Der präzise Rechteckadapter unterstützte diese transparenten Stops nicht.
Anschliessend wandelte der ältere Bandadapter die zweite Füllung in vollständig
deckende Farbbänder um, ohne ihre Stop-Deckkraft auszuwerten. Dadurch verschwand
der vertikale Hauptverlauf bereits im Raster, das der Konverter als Eingabe
erhielt. Beschreibung und Eingabebild passten nicht zusammen.

Der präzise Rechteckadapter interpoliert jetzt Farbe und Stop-Deckkraft getrennt
und verknüpft die Deckkraft mit der geometrischen Flächenabdeckung. Jede
Füllung wird einmal über den vorhandenen Hintergrund zusammengesetzt. Eine
solide Kontur behält ihre eigene Deckkraft. Quell-SVG und Vorlagen bleiben
unverändert; die Anpassung betrifft das private Renderdokument.

## Nachweise

- Analytische Regressionen prüfen zwei übereinanderliegende Farbverläufe mit
  variierender Transparenz, drei Achsenrichtungen, Translation/Skalierung und
  zwei Auflösungen. Eine Regression mit der eingefrorenen Originalvorlage prüft
  den dominierenden vertikalen Verlauf in allen 17 Workbench-Fällen.
- 83 gezielte Tests für Renderkompatibilität, lokale Verlaufsverweise und
  Workbench bestehen. Die zusätzliche Batterie für Plan-B-Varianten und den
  Linienpanel-Runtime bestand ebenfalls; ein vorübergehend von Windows
  abgebrochener HTTP-Test bestand einzeln und in der abschliessenden
  83-Test-Batterie erneut.
- Unabhängige librsvg-Vergleiche für alle 17 Referenzen in einfacher und
  zehnfacher Auflösung ergeben maximal `0.782223` mittlere Kanalabweichung auf
  der Skala 0–255 und maximal `0.000037268` normalisierten MSE. Beim Original
  sinkt der MSE gegen librsvg von `0.007172122` auf `0.000014336`.
- Die unveränderten Quellen und derselbe Seed werden durch einen neuen echten
  CLI-Diagnoselauf geprüft: **10/17 bestehen**, gegenüber **0/17** im eingereichten
  ZIP. Das Original erreicht Kantenübereinstimmung `0.962590` und
  Vordergrund-IoU `0.971182`. Kein Fall liest fremde SVG-Vorlagen. Ergebnisdetails stehen in der
  [kompakten Auswertung](../artifacts/evaluation/plan_b_transparent_gradient_2026-11-12/summary.json).

## Weiterhin offene Rekonstruktion

Die Rasterkorrektur ist keine vollständige Generalisierungsabnahme des Motivs.
Vergrösserte oder verschobene Varianten können den Rahmen am Bildrand
abschneiden. Die bestehende Linienpanel-Erkennung verwirft einige dieser
Raster bereits bei der Geradenprüfung; bei anderen unterschreitet die
registrierte Konstruktion die feste Kantengrenze. Die anschliessende
Ersatzlösung kann Linien verlieren. Diese Rekonstruktionsschwäche bleibt offen;
die Qualitätsgrenzen wurden nicht verändert.
Betroffen sind `probe_02`, `probe_03`, `probe_07`, `probe_08`, `probe_09`,
`probe_12` und `probe_16`.

Die bisherigen Nutzerläufe und das eingereichte ZIP bleiben als Fehlernachweis
erhalten. Für die korrigierten Eingaberaster ist eine neue Vorbereitung nötig;
gespeicherte alte Vorschauen ändern sich durch einen Serverneustart nicht.
Der korrigierte Lauf ist separat unter
`artifacts/gui/workbench/a14d1c33db364590bd988a78a1a92413/` abgelegt. Nach dem
Beenden zweier inaktiver paralleler Serverinstanzen verwendet der einzige
lokale Server die Korrektur; eine echte HTTP-Vorbereitung liefert pixelgleiche
Eingaben zum geprüften CLI-Lauf.
