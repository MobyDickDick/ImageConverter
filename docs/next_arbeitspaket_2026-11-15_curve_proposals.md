# FALLBACK-GROUPS-CURVE-PROPOSALS-08: beobachtete offene Kurvengruppen

Am 15.11.2026 als begrenztes synthetisches Entwicklungspaket umgesetzt.
Der produktive Fallback erzeugt jetzt native quadratische und kubische
Bézierkurven mit tangential angeschlossener gerader Linie aus Rasterbelegen.
Die unabhängige vollständige Geometrieabnahme bleibt deutlich enger als
die erreichte Rasterqualität: Nur eine der sechs neuen Konstruktionen
erfüllt bereits den eingefrorenen Kurvenvertrag.

## Produktiver Umfang

`imageCompositeConverterFallbackCurves.py` misst dünne, einfarbige, offene
Striche anhand ihrer Pixeldeckung. Pro Abtastzeile muss genau ein
zusammenhängender Strich sichtbar sein. Eine stückweise polynomiale
Regression vergleicht Q- und C-Konstruktionen mit einer geraden Zuleitung.
Die Abtastkoordinate der Kurve bleibt linear; damit ist dies eine begrenzte
Unterfamilie der allgemeinen Bézierkurven. Richtung, Position, Ausdehnung,
Farbe und Breite werden am Bild bestimmt. Es gibt keine Bild-IDs,
Katalogvorlagen oder Zugriffe auf externe Annotationen im Runtimepfad.

Native Linie und Kurve teilen tatsächlichen Endpunkt und Tangente.
Eine begrenzte Parametersuche vergleicht die gerenderten Vorschläge mit
den beobachteten Pixeln. Bei konstanten gemessenen Linienmitten konkurriert
zusätzlich eine achsenparallele Zuleitung mit der freien Steigung.
Unabhängige Kontextobjekte ziehen die lokale Registrierung nicht auf sich.
Es werden keine Rasterkonturen als Polygonzüge ausgegeben.

`group_proposals` bindet die neue Familie in den bestehenden Fallback ein.
Die Add-/Replace-Komposition verwendet dieselben bereits erzeugten
Gruppenvorschläge, statt ihre Registrierung nochmals auszuführen.
Die bestehenden Schutzprüfungen für richtige Kontextobjekte bleiben aktiv.
33 kleine Regionen folgen der tatsächlichen Kurve einschließlich ihrer
Mitte. Der produktive Relationsprüfer verlangt reale native Verbindung
und Tangente; Gruppenmarkierungen allein genügen nicht. Effekte und
Transformationen dieses begrenzten Runtimevertrags werden zurückgewiesen.

Alle Registrierungsrenderings zählen zu `session.evaluations` und zum
aktiven Bildzeitlimit. Die Strukturvorschlagsgrenze bleibt 32, die
Elementgrenze 48 und das Vergleichsbudget fünf Sekunden. Die zusätzlichen
internen Parametersuchrenderings sind separat mitgezählt; 32 Vorschläge
bedeuten ausdrücklich nicht 32 Renderaufrufe. Ein Deadline-Test verhindert
weitere Renderstarts nach Ablauf. Bei null Vorschlägen entfällt die
Kurvenregistrierung vollständig.

## Vergleich und unabhängige Gegenproben

Vor der Runtimeänderung wurden sechs neue sichtbare Rasterkonstruktionen,
die vollständigen externen Inventare und die drei bisherigen Runtimequellen
hashgebunden eingefroren. Zwei Konstruktionen (Q und C) mit je drei
Grössen-/Drehungs-/Farbvarianten sind Entwicklungsdaten, keine sechs
unabhängigen realen Familien. Drei Seeds verwenden dieselben Eingaben,
Beschreibungen, fünf Sekunden und höchstens 32 Strukturvorschläge.
Die Toleranzen des unveränderten Kurvenprüfers bleiben 0,05 Pixel für
Geometrie und 0,01 Pixel für Strichbreite; Anschluss und Tangente werden
ebenfalls mit den vorab definierten engen Grenzen geprüft.

| Prüfung | Vorher | Nachher |
| --- | ---: | ---: |
| Direkte Ausgaben: Rastergates beider Renderer | 0/18 | 18/18 |
| Direkte Ausgaben: vollständiges unabhängiges Inventar samt Geometrie und Relationen | 0/18 | 3/18 |
| Echte CLI: gespeicherte SVGs bestehen beide Rastergates | — | 6/6 |
| Echte CLI: gespeicherte SVGs bestehen den vollständigen Kurvenvertrag | — | 1/6 |
| Echte CLI: saubere Prozessabschlüsse, erste / serielle Reihe | — | 4/6 / 6/6 |

Die übrigen fünf Konstruktionen sind trotz gutem Rasterbild keine
vollständigen nativen Abnahmen: Kontrollpunkte, Anschlusslage oder
Strichbreite liegen ausserhalb der engen externen Toleranzen. Die CLI-Zahlen
bewerten gespeicherte SVGs; Laufzeitfehler und erhaltene Zwischenstände
stehen zusätzlich in den Prozessberichten und werden nicht als saubere
Prozessabschlüsse umgedeutet. Die CLI-Reihe wurde nach zwei Zeitlimits
unter gleichzeitiger Testlast separat seriell wiederholt; beide Reihen
bleiben erhalten. Die serielle Wiederholung endet in allen sechs Fällen
ohne Prozesszeitlimit; die unabhängigen SVG-Ergebnisse bleiben 6/6 und 1/6.
Es gibt keinen CLI-Vorhervergleich und keinen Nachweis
einer grösseren Katalogabdeckung.

54 beschädigte Gegenproben werden vom unabhängigen Prüfer zurückgewiesen.
42 scheitern zusätzlich an den lokalen Kurven-/Relationsprüfungen beider
Renderer. Sechs zusätzliche verdeckte Inventarfehler sind unter beiden
Renderern pixelgleich zum korrekten Bild; sie belegen erneut die Grenze
der Rasterprüfung. Zusätzliche sichtbare Duplikate können ebenfalls durch
das vollständige Inventar auffallen, obwohl lokale Verbindungsprüfungen
keine neuen Objektzahlen behaupten.

Die 15 alten CURVES-07-Konstruktionen wurden separat untersucht. Es entstehen
vier Vorschläge, aber null vollständige Szenen. Ihre zusätzlichen Ellipsen
und vollständig verdeckten Kurven werden nicht aus den Annotationen ergänzt.
`hidden_geometry_verified` ist bei den sechs neuen sichtbaren Inventaren
allenfalls formal wahr, weil sie keine verdeckten Objekte enthalten; es
belegt keine Rekonstruktion verdeckter Realbildgeometrie.

904 gezielte Regressionen und 42 Kerntests bestehen ohne Überspringungen.
CI enthält die neuen Regressionen und den Raster-/Gegenproben-Replay;
ein GitHub-Lauf wurde nicht gestartet. Die bisherigen unabhängigen Prüfer,
ihre Freezes und die Rastergrenzen bleiben unverändert.

[Gesicherte Eingaben, Ausgaben und Reproduktion](../artifacts/evaluation/curve_proposals_v1/README.md).

## Grenzen und nächstes Arbeitspaket

**FALLBACK-GROUPS-CURVE-REGISTRATION-09** folgt: Die fünf sichtbar gut
angenäherten, aber unabhängig geometrisch unbestätigten Konstruktionen
unter identischen Budgets stabil registrieren. Kontrollpunkt-, Anschluss-
und Breitenfehler einzeln ausweisen und die volle externe Abnahme verbessern;
die engen Prüftoleranzen und negativen Kontrollen bleiben verbindlich.
Die beobachteten CLI-Zeitlimits und die Registrierungskosten gehören in
denselben Vergleich. Keine neue reservierte Familie als Ersatz für diese
offenen Entwicklungsfehler ausführen.

Allgemeine Bézierparametrisierungen, elliptische Bögen, mehrere Kurven je
Gruppe, nicht eindeutig sichtbare Trennstellen, verdeckte Ergänzungen,
Schleifen, Verzweigungen, gefüllte Kurven und wechselnde Strichfarben sind
noch nicht abgedeckt. Ein menschlicher Annotationsaudit, unabhängige reale
Vollständigkeitsabnahme, SEARCH-STRUCTURE-01 und SEMANTIC-COMPLETENESS-02
bleiben offen. HC0010, Rail, AC5041 und AC5050 bleiben `sealed_unrun`.
Null Reserveversuche, null Modellfreigaben, keine Archivpromotion.
