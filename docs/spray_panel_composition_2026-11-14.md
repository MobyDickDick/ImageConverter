# Luftbefeuchter: fünf Bauteilgruppen statt einer Zickzacklinie

**Aktuelle Nutzerpräzisierung:** Die Sprühstrahlen sind inzwischen
[als gestrichelte Linien umgesetzt](spray_panel_dashed_mist_2026-11-14.md).
Die folgenden Zahlen und Grenzen dokumentieren den vorherigen v1-Stand.

Das vom Nutzer beanstandete Beispiel `AC0130_L.jpg` aus Klasse 08 ist eine
mehrteilige geometrische Komposition. Als einfaches repräsentatives Einzelzeichen
war es ungeeignet. Die Auswahl bleibt zur Fortsetzung des begonnenen Versuchs
erhalten und kennzeichnet diese Komplexität jetzt ausdrücklich. Die Beobachtung
und die Beschreibung der drei Größen nennen nun Düsen und Sprühnebel sowie den
gestrichelten Innenrahmen. Die separate Andreaskreuz-Datei `AC0130.jpg` ist davon
nicht betroffen. Die frühere Interpretation als Zickzacklinie war fachlich falsch.

## Tatsächlich ausgeführte Konvertierung

Der neue produktive Rasterpfad `SprayPanel` rekonstruiert das gezeigte L-Original
mit einer neutral benannten Rasterkopie über die reguläre `semantic-only`-CLI.
Er liest weder Katalogkoordinaten noch SVG-Vorlagen. Die kleinen vom Nutzer
gezeigten Bildausschnitte dokumentieren die Bedeutung der Teile; sie werden
nicht als eingebettete Bilder oder als Runtime-Vorlagen benutzt.

Die fünf getrennt editierbaren SVG-Gruppen enthalten:

1. Hintergrundrechteck mit horizontalem Grauverlauf und Kontur;
2. dunklen linken Balken;
3. hohes ungefülltes gestricheltes Rechteck rechts;
4. fünf kleine native Düsenpolygone am Balken;
5. fünf Sprühnebel mit je drei getrennten nativen Geraden.

Der Konverter bestimmt Positionen, Ausdehnungen und Farben aus dem Raster.
Es gibt eigene Parameter und lokale Fehlerziele für Hintergrund, Balken,
Rahmen, jede einzelne Düse und jeden einzelnen Sprühnebel: insgesamt 13
protokollierte Suchstufen. Ein frühes globales Pixelpass-Signal beendet diese
Teilprüfungen nicht. Der Versuch erhält 120 Sekunden reguläre und höchstens
180 Sekunden gesamte Bildzeit; alle Renderprüfungen respektieren denselben
Suchkontext und dessen harte Grenze. Die geprüften CLI-Läufe benötigen ungefähr
elf bis zwanzig Sekunden und 2.307 tatsächliche Renderprüfungen. Das zusätzliche Budget
ist eine Obergrenze, keine künstliche Wartezeit.

Das Ergebnis ist eine native SVG mit drei Rechtecken, fünf Polygonen und
15 Geraden. Die fünf Einzelgruppen liegen zusätzlich als eigene SVG-Dateien
vor. Keine Rastereinbettung und kein Nachzeichnen eines gespeicherten SVGs.

## Strichelung und unabhängige Nachprüfung

MuPDF ignorierte bisher die Strichelung eines nativen Rechtecks und zeichnete
den Rahmen durchgezogen. Die private Renderübergabe materialisiert numerische
gestrichelte Rechteckkonturen nun als begrenzte Pfadstücke. Die gespeicherte
SVG behält ihr natives Rechteck mit `stroke-dasharray`. Umlaufende Phase,
negative Offsets, ungerade Muster, Eckanschlüsse und der geschlossene Stoß sind
gegen librsvg geprüft. Ungültige, zu große und nicht unterstützte Muster
werden nicht geraten. Rundungen, abweichende Endkappen und `pathLength` gehören
nicht zum neuen Normalisierungsumfang.

Die neue Spektralsuche bestimmt die tatsächlich beobachtete Strichperiode
vor der lokalen Rahmenverfeinerung. Ein subpixeliges Muster, das bloß einen
gleichmäßig grauen Rahmen vortäuscht, reicht nicht: Der externe Prüflauf verlangt
zusätzlich die Korrelation der sichtbaren Hell-Dunkel-Folge beider Rahmenseiten.

| Nachprüfung der gespeicherten CLI-SVG | MuPDF | librsvg |
| --- | ---: | ---: |
| Normalisierter mittlerer quadratischer Bildfehler | 0,000352 | 0,000366 |
| Vordergrund-IoU | 0,9923 | 0,9927 |
| Kantenübereinstimmung | 0,9273 | 0,9267 |
| Korrelation der linken Strichelung | 0,941 | 0,932 |
| Korrelation der rechten Strichelung | 0,939 | 0,929 |

Beide Renderer bestehen die unveränderten globalen Gates und 13 externe
Teilregionen. Der separate Prüfer verwendet die am Original dokumentierte
Bauteilannotation, nicht die gefundenen Runtimeparameter oder Gruppennamen.
Er verbraucht alle 23 nativen Elemente, prüft die fünf Düsenanschlüsse, die
15 Strahlen und den gestrichelten Rahmen. Prüfer und Annotation sind gesondert
hashgebunden. Das ist ein gezielter Entwicklungsvertrag für dieses bekannte
Bild, kein allgemeiner Semantikprüfer oder unabhängiger realer Holdout.

Alle 29 beschädigten Gegenproben werden abgelehnt: fehlende einzelne Düsen
oder Strahlen, fehlende Grundteile, abgetrennte Düse, falscher/weißer Strahl,
doppelte verdeckte Geometrie und falscher beziehungsweise durchgezogener Rahmen.
28 dieser Gegenproben bestehen trotzdem die bisherigen globalen Pixelgates
beider Renderer. Das erklärt, weshalb die neue Detailprüfung erforderlich ist.

## Regressionen und verbleibende Grenzen

34 neue Prüfungen sichern unter anderem jeden fehlenden Bestandteil,
Deadlineabbrüche ohne Teilerfolg, beliebige Gruppennamen, die Artefaktprüfsummen
und eine separat konstruierte 50×100-Szene mit anderen Positionen und einer
anderen Strichperiode. 230 Renderer-/Vorlagen-/Kollektionstests, 123
Fallback-/Runtime-Regressionen und 42 Kerntests bestehen. Der lokale HTTP-Test
benötigt wegen der Windows-Sandbox eine Ausführung außerhalb der Sandbox;
dieser einzelne Test besteht dort. Ein zusätzlicher Kollektionstest meldete
einmal eine abweichende Wahl des neuesten bestandenen Versuchs; seine
Einzelwiederholung bestand. Dieser bestehende Sortierrandfall wurde hier nicht
verändert. CI wurde ergänzt, noch kein GitHub-Lauf.

Eine ältere Testobergrenze zählte nur die Basisverfeinerung und ließ deren
bereits vorhandene optionale Erholungssuche aus. Mit korrekter Strichelung wird
diese Suche in einem Vorlagenfall aktiv. Die Obergrenze berücksichtigt nun die
unveränderte volle Schleifenanzahl; Qualitätsgates wurden nicht gelockert.

Die aktuelle Abnahme gilt für das gezeigte 40×80-L-Original. Separate direkte
Entwicklungsproben der 30×60-M- und 20×40-S-Bilder werden noch nicht vom neuen
Detektor erkannt. Ihre korrigierte Beschreibung ist keine Behauptung eines
Konvertierungserfolgs. Allgemeine beliebige Sprühkompositionen, niedrig aufgelöste
Strichelungen und weitere Größen bleiben Folgearbeit. Das Ergebnis wird nicht
automatisch ins Archiv zufriedenstellender Konvertierungen übernommen.

[SVG, Einzelgruppen, Vergleich und Reproduktion](../artifacts/evaluation/spray_panel_v1/README.md).

Die anschliessende Nutzerbitte um eine genauere Bildbeschreibung ist ebenfalls
umgesetzt: Der aktuelle Katalogtext beschreibt die fünf Düsen, alle fünf
dreistrahligen Sprühgruppen, ihre Ausrichtung, den Helligkeitsverlauf und den
umlaufend gestrichelten Innenrahmen als sichtbare Bildbestandteile. Er enthält
keine Arbeitsanweisungen an den Konverter. Der neue CLI-Lauf mit genau diesem
Text besteht dieselben Abnahmen und erzeugt dieselben SVG-Bytes.
