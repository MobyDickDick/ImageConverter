# Versetzter Rahmen bei AC0512_S

Die Vorlage enthält ein vollflächiges graues Rechteck und darüber ein
Verlaufsrechteck mit Kontur. Letzteres beginnt bei y=1,5 statt y=0,5;
dadurch bleibt oben ein zusätzlicher Pixel der hinteren Fläche sichtbar.
Die bisherige gemeinsame Ausrichtung konnte diesen inneren Versatz nicht ändern.

Die Vorlagensuche vergleicht nun kleine Korrekturen der Rahmenkanten mit den
Kanten der hinteren Rechteckfläche. Elemente, Innenlinien und Eingabedatei
bleiben erhalten. Die Vorschläge sind motivunabhängig und verwenden weiterhin
die Beschreibungs- und Bildprüfung. Eine zusätzliche Kontur im Original bleibt
erhalten, wenn ihre Entfernung den Vergleich verschlechtern würde.

Ausserdem unterstützt der Renderer positive gleichmässige SVG-Matrizen wie
entsprechende translate/scale-Transformationen. Zuvor fiel selbst eine
Identitätsmatrix beim Verlaufsrechteck auf eine andere Näherung zurück.
Weitere Farbanpassungen dürfen ein bestandenes Ergebnis nicht unter die
Bildgrenzen oder die bisherige gemeinsame Kontur-/Flächenbewertung drücken.

Der echte Vorlagenlauf mit Seed 17 verschiebt die obere Rahmenkante auf y=0,5
und setzt die Höhe auf 19. Pixelfehler: 0,002369 → 0,001829;
Vordergrund-IoU: 0,887 → 0,943; Kantenübereinstimmung: 0,734 → 0,757.
Die unveränderten Qualitätsgrenzen und die Beschreibung sind bestanden.
Das strengere vorzeitige Suchziel ist weiterhin nicht erreicht.
`AC0512_S.json` dokumentiert den Lauf; `comparison.png` zeigt Original,
unveränderte Vorlage und korrigiertes Resultat. `previous_result.svg` sichert
das zuvor im Projekt gespeicherte Ergebnis.

Regressionen: `tests/test_sample_frame_inset.py` prüft beide Kantenrichtungen,
unveränderte Innenlinien und Sample-Dateien, eine tatsächlich vorhandene
Zusatzkante, Matrixdarstellung, das gemeldete JPEG und einen echten GUI-Worker
unter neutralem Uploadnamen. Die Vorlagen-, Orientierungs- und Renderer-Tests
werden zusätzlich ausgeführt.

Ein bereits laufender Webserver muss nach Abschluss laufender Aufträge neu
gestartet werden, damit neue Worker den geänderten Renderer verwenden.
