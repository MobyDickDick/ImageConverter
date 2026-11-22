# Freie Suche aus beschriebenen Grundformen

Stand: 22. November 2026.

Die Einzelkonvertierung bietet zusätzlich **Freie Grundformensuche · 5 Minuten**
und **10 Minuten**. Diese Profile umgehen die Auswahl vorbereiteter Motivmodelle
und vorhandene SVG-Vorlagen. Die ursprüngliche Beschreibung bestimmt die
erlaubten Elemente. Positionen, Grössen und Winkel werden nicht aus Konturen
vermessen oder aus einem Referenz-SVG übernommen.

## Bedienung und Speicherung

Bild und Beschreibung laden, ein freies Suchprofil wählen und starten. Ein
bestandener vollständiger Bild- und Beschreibungsvergleich beendet die Suche
früher. Bei den unten beschriebenen Rand- und Verlaufsvorgaben wird bis zum
strengeren bestehenden Suchziel weiter verbessert; bereits bestandene Stände
bleiben dabei erhalten. Andernfalls rechnet sie bis zur Zeitgrenze weiter. Ein kleiner Rest des
gemeinsamen Bildbudgets bleibt für Speichern und Rückgabe an den Worker frei.

Alle fünf Sekunden werden Population, bester Stand, bisher geprüfte Kandidaten
und Zustand des Zufallsgenerators atomar gespeichert. Ein erneuter Start mit
denselben Bildpixeln, derselben effektiven Beschreibung und demselben Seed setzt
diesen Suchstand fort. Ein anderer Seed erhält einen eigenen Ordner. Ein
geänderter Dateiname allein eröffnet keine neue Suche. Geänderte Pixel oder
Beschreibung dagegen schon. Beim Laden wird ein gespeicherter Erfolg erneut
gerendert und geprüft; gespeicherte Erfolgskennzeichen ersetzen keine Prüfung.

Die Oberfläche legt diese Daten unter
`<GUI-Datenverzeichnis>/primitive-search-memory/<Inhaltsschlüssel>/` ab:

- `checkpoint.json`: Population, Parameter, Seed, RNG-Zustand und Kandidatengedächtnis.
- `candidates.jsonl`: tatsächliche geprüfte Varianten mit Operator, Parametern,
  Bewertung sowie getrennten Identitäten für SVG und Geometrie.
- `best.svg` und `solution.json`: bester gespeicherter Stand und interpretierbare
  Konstruktion samt Prüfstatus. Ein fehlgeschlagener Stand ist ausdrücklich keine Lösung.
- `variant-*.svg`: ausgewählte Verbesserungen zur Kontrolle der Suchentwicklung.
- `report.json`: Abschlussgrund, Renderzahlen, Vielfalt, Laufzeit und Qualitätswerte.

Ein OS-Dateilock verhindert, dass zwei Aufträge denselben Suchstand gleichzeitig
überschreiben. Nach Abbruch oder Prozessende gibt das Betriebssystem den Lock
frei. Beim nächsten Start wird der letzte vollständige Checkpoint verwendet;
höchstens die Arbeit seit der letzten Speicherung geht verloren.

Erfolgreiche SVGs werden wie andere GUI-Ergebnisse im Projekt gespeichert. Die
bestehende Qualitätsauswahl erhält eine schon bessere Projektversion. Im
Versuchsfenster sind auch verworfene und schlechtere Renderkandidaten sichtbar.

## Suchverfahren

Eine Population beginnt mit mindestens 32 unabhängig zufälligen Anordnungen.
Die Suche kombiniert neue vollständige Anordnungen, Austausch einzelner Objekte,
Vertauschen ihrer Platzierungen, Objekt-Crossover, Differenzmutation, grosse
Änderungen und lokale Verfeinerung. Häufige rechte Winkel sind zusätzliche
Winkelvorschläge, keine einzige festgelegte Ausgangsgeometrie.

Beschriebene Verbindungen können durch einen allgemeinen Operator verbunden
werden. Solche Kandidaten bleiben als eigene Suchzweige erhalten, auch wenn sie
zunächst schlechter als ein unverbundener Kandidat aussehen. Zufällige neue
Zweige werden ebenfalls nicht allein wegen einer schlechteren Anfangsbewertung
sofort verworfen. Die beste gültige Konstruktion bleibt erhalten.

Die Auswahl berücksichtigt Pixeldifferenzen, Vordergrundüberdeckung,
Kantenabstände und beschriebene Beziehungen. Die bestehenden endgültigen
Pixelgrenzen bleiben unverändert. Gemeinsame Spitzen werden am ausgegebenen SVG
mit numerischer Toleranz 0,01 Pixel geprüft. Eine gute Pixelähnlichkeit allein
erlaubt kein SVG mit getrennten beschriebenen Verbindungspunkten.

Nur wirksame Parameter einer Form werden lokal verändert. Beispielsweise sind
Kreisdrehung und Linienfüllung keine zusätzlichen Suchdimensionen. Der
Geometriezähler ignoriert reine Farbänderungen und bedeutungslose Parameter.

## Unterstützter Umfang und Grenzen

Der begrenzte Übersetzer unterstützt einfache Listen aus Kreis, Ellipse,
Rechteck, Quadrat, Dreieck und Linie, bis zu zehn Elemente. „Kelle mit Griff“
wird einmal allgemein zu Kreis und Linie aufgelöst. Unterstützt sind die vier
Griffrichtungen, gemeinsame Spitzen beziehungsweise Griffendpunkte sowie
einfache Abschnitte „Links:“ und „Rechts:“. Wiederholte Referenzen auf dieselben
Dreiecke werden nicht als zusätzliche Dreiecke gezählt. Dreieckvorschläge sind
derzeit gleichschenklig, auch wenn der Text diese Eigenschaft offenlässt.

Zusätzliche vollständige Sätze dürfen die Ränder und Verläufe einer Formgruppe
festlegen, beispielsweise „Beide Dreiecke haben gleich breite Ränder“ und
„Beide Dreiecke haben je einen Farbübergang (hellgrau nach dunkelgrau)“.
Dies gilt ebenso für Kreise, Ellipsen, Rechtecke und Quadrate; „alle“ und „die
beiden“ sind weitere unterstützte Gruppenangaben. Nur die genannte Formgruppe
teilt ihre Randbreite. Jeder verlangte Verlauf braucht unterschiedliche,
sichtbare Farbstopps. Die Grauangaben bestimmen einen Helligkeitsbereich und
die Reihenfolge der Stopps; sie legen keinen einzelnen RGB-Code fest.

Diese Vorgaben gelten auch für normale Profile, Vorlagen und Entwürfe. Native
Kreis-/Linien-/Dreieckvorlagen können als Anfangsgeometrie weiterverwendet werden;
die freie Suche beginnt weiterhin unabhängig von solchen Vorlagen. Gespeicherte
Suchstände mit älterem Programm- oder Rendererstand werden getrennt behandelt.
Ein anderer Seed erzeugt andere tatsächliche Suchfolgen, garantiert aber kein
anderes Endergebnis, wenn mehrere Suchen zur gleichen guten Lösung gelangen.

Es ist kein vollständiger Freitextparser. Unter anderem Textzeichen,
weitere explizite Farbangaben, allgemeine Symmetrie- und Parallelitätsbedingungen,
gestrichelte Linien und weitere komplexe Motive werden von diesem neuen Pfad
noch nicht vollständig unterstützt und deshalb vor dem Start abgewiesen.
Andere vorhandene Profile behalten ihre bisherigen Beschreibungsmodelle.
Nicht genannte Farben werden als Suchparameter am Original angepasst.

Die Zeichenreihenfolge ist derzeit fest; freie Schichtpermutationen sind noch
kein Suchoperator. Die Erfolgswahrscheinlichkeit hängt vom Suchraum, Seed und
Budget ab. Mehr verschiedene Varianten sind kein Beleg für einen sicheren Erfolg.
Ein unabhängiger Kontrollfall mit Kreis und Rechteck blieb in den dokumentierten
Versuchen unterhalb der Qualitätsgrenze. Eine allgemeine Erfolgsquote ist nicht belegt.

Gespeicherte Populationen gehören genau zu ihrer Eingabe. Sie werden nicht
automatisch als Vorlagen anderer Bilder geladen und trainieren kein Modell.

## CLI

```powershell
.venv/Scripts/python.exe -m src.imageCompositeConverter INPUT `
  --descriptions-path BESCHREIBUNGEN.xml --output-dir OUTPUT `
  --start FIRST --end LAST --primitive-exploration `
  --primitive-memory artifacts/primitive-search-memory `
  --search-seed 42 --search-seconds 300 --search-max-seconds 300 `
  --search-budget 1000000
```

Für zehn Minuten beide Sekundenwerte auf 600 setzen. Die höhere Rendergrenze
ist nur für die explizite freie Suche zugelassen; normale Profile behalten ihre
bisherige Grenze. Zeit und echte Renderzahl werden weiterhin durch den
gemeinsamen Bildkontext überwacht.

[Messungen und Prüfnachweise](../artifacts/evaluation/primitive_evolution_2026-11-21/README.md).
