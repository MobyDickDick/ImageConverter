# P0-Abschluss: unabhängige Rasterabnahme dünner Rechteckseiten

**SVG-CLIPPED-SIDE-RENDERER-01**, synthetischer Teilumfang **abgeschlossen**.
Folge des [angeschnittenen Rechteckpakets](next_arbeitspaket_2026-11-07_clipped_rectangular_parent.md).

## Umsetzung und Abnahme vom 11.11.2026

Der private Rasteradapter integriert die Pixelabdeckung scharfer
Verlaufsrechtecke einschließlich ihrer zentrierten Kontur direkt am
Ausgaberaster. Jede vormultiplizierte 8-Bit-Überlagerung wird einzeln
quantisiert. Gespeicherte SVGs behalten native Rechtecke, unveränderte
Geometrie, Konturen und Verläufe. Gerundete Formen und nicht unterstützte
Kontur-/Transformationsfälle verwenden weiterhin den vorhandenen Pfad.

Die beobachtete Abweichung kombiniert MuPDFs begrenzte Kantenabtastung mit
Farbquantisierung: winzige Deckungsanteile gehen verloren, beziehungsweise
eine getrennte Schlussrundung von Farbe und Alpha erzeugt einen Farbsaum.
Dadurch wählt Cannys Nichtmaximumunterdrückung bei fast gleichen Gradienten
eine benachbarte Pixelposition. Die gesicherten Profile enthalten reale
BGR-Werte und tatsächliche Canny-Positionen beider Renderer. Die Anzahl der
Kantenpixel allein konnte den Fehler nicht erkennen; eine Lockerung der
Hysterese oder der Kantenübereinstimmung wurde nicht benötigt.

Die Registrierung prüft kleine gemeinsame Verschiebungen und symmetrische
Größenänderungen gegenüberliegender Grenzen vor der einzelnen
Koordinatensuche. Eine einzelne verschobene Seite verändert zugleich das
Verlaufsfeld und konnte trotz guter lokaler Seite die anfängliche
Pixelerrorgrenze verletzen. Diese Grenze bleibt verbindlich. Bereits
vollständig geprüfte Startmodelle benötigen keine alternativen Startwerte;
das vermeidet einen neuen Budgetfehler beim zuvor bestandenen Zusatzfall 08.

| Unveränderte Kohorte | Vorher | Nachher, beide Renderer und alle lokalen Gates |
| --- | ---: | ---: |
| Eingefrorene Renderer-Kontrollen | 21/26 | 26/26 |
| Echte CLI, Hauptseed 718293 | 12/12 | 12/12 |
| Echte CLI, Zusatzseed 391827 | 10/12 | 12/12 |
| Echte CLI, gekoppelte Varianten 718293 | 17/17 | 17/17 |

Alle 41 endgültigen CLI-Ausgaben bestehen native Objekt-/Relationsgates,
globale, objektlokale, sichtbare Eck-/Seiten- und Restbildprüfungen.
Alle Eingabe-, Referenz- und Beschreibungsprüfsummen bleiben erhalten.
Fünf Sekunden, 96 Strukturzustände, alle Qualitätsgrenzen und die
anfängliche Pixelerrorgrenze sind unverändert. Keine Datei- oder
Familienkennung steuert die Korrektur; Referenz-SVG-Zugriffe der CLI bleiben
gesperrt. Die beiden ursprünglichen Ablehnungen und zwei lokale
Entwicklungszwischenstände bleiben getrennt erhalten.

Die neuen eingefrorenen Kontrollen decken Subpixellagen, Konturbreiten
1/1,5/3 Pixel und beide Verlaufsachsen ab. Zwei unveränderte Originalfälle
sind zusätzlich direkt als Registrierungsregressionen abgesichert.
Analytische Pixeldeckungsprüfungen kontrollieren auch ViewBox und gemeinsame
Translation/Skalierung. Breitere Szenen-/Renderer-/Budgetregressionen und
das Kernprofil stehen mit Befehlen, Exitcodes und Ergebnissen im
[Nachweis](../artifacts/evaluation/clipped_side_renderer_v1/README.md).
Der CI-Job verlangt jetzt außerdem alle 26 eingefrorenen Kontrollen und die
vollständige Zusatzkohorte; ein GitHub-Lauf wurde hier nicht gestartet.

HC0010 und Rail bleiben nach schreibfreier Integritätsprüfung `sealed_unrun`.
SEARCH-STRUCTURE-01, GENERAL-SCENE-COMPOSITION-09 und die unabhängige reale
Abnahme bleiben offen. Das ist ein synthetischer Teilabschluss ohne
Kataloggewinn. Nächster übergeordneter Schritt ist die weitere gemeinsame
Strukturkomposition mit vorab gesicherten unabhängigen realen Prüffamilien;
die vorhandene Reserve darf erst mit vollständigen Prüfern offengelegt werden.

## Ursprünglicher gesicherter Befund

Die unabhängige Zusatzkohorte `391827` enthält den scharfen Fall
`clipped_rectangle_10`. Sein unverändertes Referenz-SVG besteht die native
Objekt-/Geometrieprüfung und die globale MuPDF-Rasterprüfung. Mit librsvg
bestehen alle sichtbaren Seiten; MuPDF verfehlt zwei Seiten mit
Kantenübereinstimmung ungefähr `0,6924` und `0,4769` bei Mindestwert `0,72`.
Die Abweichung tritt bereits beim exakten Referenz-SVG auf und ist damit
von der rekonstruierten Geometrie zu trennen. Die neue Suche erhält für
diesen Fall keinen stillen Erfolg. Das ist keine reale Familienabnahme.

Der zweite Zusatzfall `clipped_rectangle_02` bleibt ebenfalls nach fünf
Sekunden ohne geprüften Zwischenstand. Seine exakten Referenzkontrollen
bestehen mit beiden Renderern einschließlich Seiten und Ecken. Hier liegt
eine getrennte Registrierungsgrenze vor; sie darf nicht dem Rendererfehler
zugerechnet oder aus dem Zusatznenner entfernt werden. Beide unveränderten
Fälle gehören zur Abnahme des Folgepakets.

## Verbindlicher Lieferumfang (umgesetzt)

1. Originalraster, Referenz-SVG, Beschreibungs-/Objekt-/Relationsmarkierungen,
   Renderer- und Runtimeversionen sowie die vorhandenen Prüfsummen sichern.
   Weitere unabhängige Seitenkontrollen für Subpixellagen, dünne Konturen,
   ähnliche Kontur-/Füllfarben und Verlaufsachsen vor Änderungen einfrieren.
2. Seitenprofile und tatsächliche Canny-Kanten beider Renderer vergleichen.
   Antialiasing, Farbquantisierung, Konturgeometrie und lokale Hysterese
   voneinander unterscheiden. Kein Rückschluss auf Generatorgeometrie im
   Konverter; keine bildnamenabhängige Korrektur.
3. Den allgemeinen Raster-/Registrierungspfad am beobachteten Fehler
   korrigieren. Kanten-, Pixel-, native Objekt-/Relations- und anfängliche
   Fehlergrenzen nicht lockern. Einen Referenzrenderfehler nicht durch
   dauerhaft falsche native Geometrie kompensieren.
   Den separat belegten Registrierungsfehler von `clipped_rectangle_02`
   unter demselben Bildbudget beheben; Hypothesen und lokale Ablehnungsgründe
   getrennt protokollieren.
4. Identische gesicherte Haupt-, Zusatz- und Variantenraster durch die echte
   CLI prüfen. Alle sichtbaren Seiten und Ecken, jedes Objekt und das
   Restbild mit beiden Renderern abnehmen; Ablehnungen im Nenner belassen.
   Fünf Sekunden und 96 Strukturzustände erhalten.
5. Vollständig sichtbare scharfe/gerundete Eltern, angeschnittene Kreise,
   Konturfarben, Tiefenbelege und die negativen Beobachtbarkeitskontrollen
   regressionsprüfen. HC0010 und Rail bleiben `sealed_unrun`.

## Start

```powershell
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --prepare .tmp/clipped-side-controls --seed 391827
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --inputs .tmp/clipped-side-controls --output .tmp/clipped-side-cli
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --inputs .tmp/clipped-side-controls --output .tmp/clipped-side-cli --audit .tmp/clipped-side-audit.json
```

Der [Nachweis des Vorgängerpakets](../artifacts/evaluation/clipped_rectangular_parent_v1/README.md)
enthält den exakten Kontrollvergleich und die vollständigen Fehlversuche.

## Sitzungslog

- Getestet: 26 eingefrorene Renderkontrollen, 41 echte CLI-Fälle mit beiden Renderern, Szenen-/Renderer-/Budgetregressionen und Kernprofil.
- Ergebnis: 26/26, 41/41, 398/398 Regressionen und separat 42/42 Kerntests; sämtliche endgültigen Befehle Exit 0, keine Überspringungen.
- Grenzen: Synthetischer Teilabschluss; keine unabhängige reale Abnahme oder Archiv-Neukonvertierung, HC0010/Rail bleiben versiegelt.
- Nächster Schritt: SEARCH-STRUCTURE-01 / GENERAL-SCENE-COMPOSITION-09 fortsetzen; neue reale Prüffamilien vor Entwicklung sichern und Reserve nur mit vollständigen Prüfern offenlegen.
- Startbefehl: `.venv/Scripts/python.exe -m tools.evaluate_clipped_side_renderer --controls tests/fixtures/clipped_side_renderer --report .tmp/clipped-side-replay.json --require-all`.
