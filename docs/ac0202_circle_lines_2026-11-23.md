# AC0202_1: farbiger Kreis mit zwei gespiegelten Linien

Die bereits im Arbeitsverzeichnis vorhandene Benutzerbeschreibung bleibt
unverändert: grauer Kreisrand, rote Füllung, zwei weisse Linien mit Randkontakt
und Spiegelung an der horizontalen Mittellinie. Genau diese Beschreibung wird
in beiden XML-Katalogkopien versioniert. Andere uncommittete Katalog- und
Sample-Änderungen sind nicht Bestandteil der Korrektur.

## Nachgewiesene Ursachen

Der unveränderte Ausgangscommit `13a52bb03033987fd4861877c3fbf0bd10c52d5c`
lief auf GitHub mit einem anonymisierten Upload und derselben Beschreibung:

- Die allgemeine Heuristik meldete `SEMANTIC: Kreis + Buchstabe`. Ihr Modell
  konnte die beschriebenen Linien nicht erzeugen.
- Die allgemeine Objektzählung interpretierte die horizontale Hilfslinie zur
  Definition der Symmetrie als dritte sichtbare Linie. Das Protokoll endete mit
  `DescriptionRejected: logical_object_count:line:3:0`.
- Nach 120 tatsächlichen Renderings endete die Suche mit `models_exhausted`,
  ohne verwendbares SVG. Das Zeitlimit war nicht erreicht.
- Der vorhandene Kreis-Linien-Fitter akzeptierte nur einen eng festgelegten
  Text über einen grauen Kreis mit dunklen Linien. Er suchte ausschliesslich
  dunkle Striche und reduzierte Farben auf Grautöne. Eine blosse zusätzliche
  Textalternative hätte die farbige Variante deshalb noch nicht behoben.
- Das zuvor gespeicherte Projekt-SVG enthielt eine Ellipse und beinahe
  senkrechte Linien. Es liegt unverändert als negative Testvorlage in
  `tests/fixtures/colored_circle_wrong_axis.svg`.

Der [GitHub-Vergleichslauf](https://github.com/MobyDickDick/ImageConverter/actions/runs/45117688880)
enthält Protokolle und Artefakte beider Stände. Der Baseline-Job ist eine
Diagnose: Sein erfolgreicher Abschluss bedeutet, dass der Fehler aufgezeichnet
wurde, nicht dass der alte Konverter das Bild erfolgreich konvertiert hätte.

## Korrektur

Der Parser erkennt die vollständige Beschreibung vor der Badge-Heuristik.
Der Vertrag verlangt genau einen Kreis und zwei sichtbare Linien; die
Symmetrieachse fügt kein drittes Objekt hinzu. Unverbrauchte zusätzliche
Angaben werden von diesem begrenzten Modell nicht stillschweigend ignoriert.

Die Registrierung bestimmt Kreis, Linienrichtung, Abstände, Strichbreiten
und Füllfarbe aus den Bildpixeln. Helle und dunkle Striche werden getrennt
erfasst. Die rote Füllung behält ihre Farbkanäle; grauer Rand und weisse Linien
werden als neutrale Farben angepasst. Die Linienenden folgen dem Schnitt
mit der inneren Randkante. Spiegelung und Randkontakt bleiben dadurch bei
jeder Verfeinerung erhalten.

Die abschliessende Beschreibungsprüfung verwirft Ellipsen, fehlende Linien,
falsche Spiegelung und abgelöste Endpunkte auch bei Entwürfen. Ein altes SVG
kann den neuen Lauf nicht mehr als vermeintlich gültiger Beststand ersetzen.
Es gibt keine bildnamenspezifische Geometrie und keine abgesenkten Pixelgrenzen.

## Validierung

Alle Tests und Konvertierungen laufen ausschliesslich auf GitHub Actions.
Im verlinkten Lauf bestehen 94 gezielte Tests und alle vier echten
Konvertierungen. Der unabhängige librsvg-Vergleich ergibt:

| Profil | Seed | Altes SVG | Vordergrund-IoU | Normierter MSE | Ergebnis |
|---|---:|---|---:|---:|---|
| quick | 17 | aus | 0,99129 | 0,001666 | bestanden |
| quick | 18 | aus | 0,99304 | 0,001677 | bestanden |
| normal | 17 | aus | 0,99129 | 0,001666 | bestanden |
| quick | 17 | an, absichtlich falsch | 0,99129 | 0,001666 | bestanden |

Die echten freien Suchen mit Seeds 17/18 benötigen 347 bzw. 353 Renderings
und haben unterschiedliche Renderfolgen. Der Verlauf ist kein gespeichertes
Katalogbild. Das veröffentlichte `AC0202_1.svg` stammt aus dem quick-Lauf mit
Seed 17; die kompakten Messwerte stehen unter
`artifacts/evaluation/ac0202_circle_lines_2026-11-23/summary.json`.

Der gezielte Job umfasst die unveränderte Beschreibung, echte GUI-Worker mit
Seeds 17/18 und Profilen quick/normal, Wiederverwendung der fehlerhaften alten
Vorlage, synthetische farbige Quellen in beiden Spiegelachsen und die Prüfung
des tatsächlich versionierten SVGs. MuPDF und der unabhängige librsvg-Renderer
prüfen die Bildqualität.

Die vorhandenen Kreis- und Vorlagentests laufen zusätzlich unverändert gegen
Ausgangsstand und Korrektur. Der Vergleich verlangt dieselbe Testmenge, keinen
Einrichtungsfehler und keine neu hinzugekommenen Fehler. Bestehende rote Jobs
bleiben sichtbar; der gesamte Workflow darf deshalb trotz bestandener
Konvertierung nicht als vollständig grün bezeichnet werden.

In beiden verglichenen Ständen bestehen 22 vorhandene Tests; dieselben fünf
schlagen fehl. Der Vergleichsjob bestätigt keine zusätzlichen Fehler:

- Der AC0201-Katalogtest erwartet einen älteren exakten Beschreibungstext.
- Zwei Vorlagentests erwarten eine andere Auswahl bzw. byteidentische
  SVG-Serialisierung.
- Beide vorhandenen Rechteck-Kontrastkonvertierungen enden mit Fehler.

Die übrige projektweite CI ist ebenfalls nicht vollständig grün. Diese
Korrektur beansprucht keine bestandene Gesamtabnahme aller Konverterfamilien.

Die Änderung erweitert einen begrenzten deutschen Sprachumfang. Sie ist kein
allgemeines Verständnis beliebiger Kreis-, Linien- oder Symmetriebeschreibungen.
