# Aufgabenplan: generische Bild-und-Beschreibung-zu-SVG-Konvertierung

## Projektziel

Gegeben sind ein Rasterbild und eine Bildbeschreibung. Daraus soll der Konverter
ein SVG mit optimaler Qualität erzeugen, gemessen primär an der Fehlerquote der
Pixelfehler zwischen gerendertem SVG und Zielbild.

## Leitentscheidung

Die bisherige Aufgabenliste wird von vielen formbezogenen Einzelarbeiten auf
wenige, überprüfbare Produktziele verdichtet. Priorität haben nur Arbeiten, die
entweder die Pixelmetrik verbessern, form-/bild-ID-spezifische Runtime-Logik
entfernen oder die Reproduzierbarkeit der Qualitätsentscheidung erhöhen.

Nicht mehr priorisiert werden weitere Kandidaten-Feinschritte, die nur einen
einzelnen Bildcode stabilisieren und keinen wiederverwendbaren Algorithmus
verbessern.

## Umgeordnete Roadmap

### P0 – Qualitätsziel und Messverfahren fixieren

1. [ ] Eine zentrale Qualitätsdefinition festlegen: Primärmetrik
   `mean_delta2`, sekundär `normalized_mse`, Kantenfehler und Laufzeit.
2. [ ] Akzeptanzschwellen je Bildklasse definieren: einfache Symbole,
   Text-/Badge-Symbole, Mehrkomponentenbilder und breite/hohe Sonderformate.
3. [ ] Einen reproduzierbaren Holdout-Satz festlegen, der nicht als
   Bild-ID-Sonderlogik im Runtime-Code verwendet werden darf.
4. [ ] Einen täglichen oder manuellen Quality-Report erzeugen, der Baseline,
   aktuelles Ergebnis, Regressionen und Top-Fehlerfälle in einer Datei bündelt.

### P1 – Harte Bild- und Formabhängigkeiten entfernen

5. [x] Formcode-Inventar automatisch erzeugen.
6. [ ] Runtime-Treffer in `erlaubt` und `nicht erlaubt` klassifizieren.
7. [ ] CI-Guard aktivieren, der neue bild-/form-ID-spezifische Branches in
   Runtime-Modulen blockiert.
8. [ ] Bestehende Sonderpfade nur dann behalten, wenn sie als generisches
   Primitive-, Topologie- oder Optimierungsverhalten formuliert sind.

### P2 – Einheitliche Zwischenrepräsentation etablieren

9. [ ] Schema v1 für Geometry-IR/Umsetzungsbeschreibung festschreiben:
   Primitive, Parameterbereiche, Constraints, Style-Layer und Objective-Weights.
10. [ ] Loader und Validator für diese Beschreibung integrieren.
11. [ ] Bildbeschreibung, Perception-Seeds und vorhandene Heuristiken in dieselbe
    IR übersetzen, statt getrennte Pfade für einzelne Familien zu pflegen.
12. [ ] SVG-Emission ausschließlich aus der IR ableiten.

### P3 – Initialisierung aus Bild und Beschreibung verbessern

13. [ ] Beschreibungsparser auf eine kleine, stabile Vokabularschicht reduzieren:
    Formen, Lage, Größe, Farbe, Anzahl, Text/Glyphen und Wiederholungsmuster.
14. [ ] Perception-Seeds für Kanten, Farbfelder, Linien, Polygone, Kreise/Ringe
    und Textbereiche vereinheitlichen.
15. [ ] Fusion-Regel festlegen: Beschreibung bestimmt Topologie-Prioren,
    Bildsignal bestimmt konkrete Parameter, Pixelmetrik entscheidet.
16. [ ] Fehlende oder widersprüchliche Beschreibungsteile mit niedriger
    Konfidenz markieren, nicht durch Bild-ID-Wissen ersetzen.

### P4 – Generische Optimierung statt Einzelbild-Tuning

17. [ ] Coarse-to-fine-Optimierung für alle IR-Primitive vereinheitlichen.
18. [ ] Multi-Start-Strategie für lokale Minima einführen.
19. [ ] Adaptive Schrittweiten je Parameterklasse implementieren: Position,
    Größe, Stroke, Farbe, Opacity, Gradient und Text.
20. [ ] Elementweise Verbesserungen nur übernehmen, wenn die gerenderte
    Pixelmetrik strikt besser wird.
21. [ ] Optionalen globalen Suchschritt nach der Elementoptimierung anwenden,
    begrenzt durch Laufzeitbudget und Regressionstest.

### P5 – Fehleranalyse produktiv machen

22. [ ] Für jeden Top-Fehlerfall automatisch die Fehlerklasse bestimmen:
    falsche Topologie, schlechte Initialisierung, Farbfehler, Kantenversatz,
    Text/Glyphenfehler, Antialiasing oder lokales Minimum.
23. [ ] Pro Fehlerklasse genau eine generische Verbesserungsaufgabe ableiten.
24. [ ] Kandidatenrotation auf maximal fünf aktive Fälle begrenzen und nur als
    Diagnose verwenden, nicht als Implementierungsgrund für Sonderlogik.
25. [ ] Fehlschlagberichte mit Reproduktionskommando, Metrik vorher/nachher und
    erwarteter generischer Verbesserung ablegen.

### P6 – Regression und Abschluss

26. [ ] Smoke-Tests für Parser, IR, Renderer, Optimierer und SVG-Emission bündeln.
27. [ ] Holdout-Regression gegen bild-ID-unabhängige Namen ausführen.
28. [ ] Qualitätsregression blockieren, wenn ein akzeptierter Fall sichtbar oder
    metrisch signifikant schlechter wird.
29. [ ] Abschlusskriterium: keine verbotene Runtime-Sonderlogik, stabile
    Reproduzierbarkeit und ein priorisiertes generisches Backlog für die
    verbleibenden Fehlschläge.

## Gekürzte nächste 10 Aufgaben

1. [ ] Aktuellen Quality-Report erzeugen und die fünf größten reproduzierbaren
   Fehlerfälle bestimmen.
2. [ ] Runtime-Formcode-Inventar aktualisieren und nicht erlaubte Treffer
   markieren.
3. [ ] CI-Guard gegen neue Runtime-Bildcodes scharf schalten.
4. [ ] Geometry-IR-Schema v1 in einem kleinen JSON/YAML-Vertrag festlegen.
5. [ ] Loader/Validator für den Vertrag implementieren.
6. [ ] Einen einfachen Kreis-/Ringfall vollständig über IR statt Sonderlogik
   konvertieren.
7. [ ] Eine generische Coarse-to-fine-Optimierung für mindestens drei Primitive
   nachweisen.
8. [ ] Beschreibung-Bild-Fusion für Formen, Farben und Positionen vereinheitlichen.
9. [ ] Top-Fehlerfälle automatisch klassifizieren und daraus generische
   Optimierungsaufgaben erzeugen.
10. [ ] Holdout-Regression ausführen und die Roadmap anhand der Metriken neu
    sortieren.

## Streichungen gegenüber der alten Liste

- Einzelne Familien-Migrationslisten ohne direkte Messwirkung werden gestrichen.
- Pflichtartefakte pro Form werden nur noch für Top-Fehlerfälle erstellt.
- Manuelle Plan-B-Feinschritte bleiben erlaubt, zählen aber nur als erledigt,
  wenn daraus eine wiederverwendbare IR-, Perception- oder Optimierungsregel
  entsteht.
