# FALLBACK-GROUPS-CURVES-07: unabhängiger nativer Kurvenvertrag

Am 15.11.2026 als begrenztes synthetisches Prüferpaket abgeschlossen.
Die Fortsetzung des Katalogaudits nach FALLBACK-GROUPS-CLEANUP-06 bestätigt
15 positive Konstruktionen und verwirft 285 beschädigte Gegenproben.
45 davon sind mit MuPDF und librsvg jeweils pixelgleich zum korrekten Bild.
Der neue Prüfer erkennt trotzdem fehlende, zusätzliche und geometrisch
veränderte verdeckte Kurven. Die bestehenden Geradenprüfer, ihre separaten
Freeze-Dateien und die produktiven Rastergates bleiben unverändert.

## Vertrag und unabhängige Konstruktion

`tools.check_curve_scene.check_scene(svg, annotation)` verlangt das Schema
`independent_curve_scene_v1` und ein vollständiges externes Inventar.
Native quadratische und kubische Bézierkurven werden mit sämtlichen
Kontrollpunkten geprüft. Elliptische SVG-Bögen werden aus Endpunkten,
Radien, Achsrotation und beiden Bogenflags geometrisch normalisiert:
Mittelpunkt, Ellipsenform, Bogenmitte und Öffnungswinkel müssen zur
unabhängig konstruierten Annotation passen. Die SVG-Radienkorrektur wird
berücksichtigt. Handberechnete Kreis-/Ellipsenfälle prüfen beide Bogenäste
und die Radienkorrektur zusätzlich zum synthetischen Replay.

Jeder Kurvenpfad enthält genau ein `M` und ein `Q`, `C` oder `A`.
Absolute und relative Koordinaten, umgekehrte Laufrichtung, verschachtelte
Attributvererbung sowie Translation, Rotation, uniforme Skalierung und
Spiegelung sind erlaubt. Zulässig sind ungefüllte, sichtbare Einzelstriche;
Farbe, Strichbreite, Endkappen und Linienübergänge gehören zum Vertrag.
Alle nativen Bestandteile einschließlich Hintergrund und Deckobjekten
werden injektiv genau einmal zugeordnet. Die Suche ist auf 48 Objekte
und 4.096 Zuordnungsschritte begrenzt.

`endpoints_meet` prüft tatsächliche Endpunkte. `tangent_join` verlangt
zusätzlich entgegengesetzte nach innen gerichtete Tangenten am Anschluss.
Kontrollpunkte zählen nicht als Anschlusspunkte; die Gerade zwischen
Kurvenendpunkten ersetzt keine Kurventangente. `front_of` bindet die
Zeichenreihenfolge. Die Entwicklungsszenen verwenden 0,05 Pixel
Geometrietoleranz, 0,01 Pixel Anschlussabstand und 0,1 Grad Tangentenwinkel.
Die Obergrenzen des Vertrags bleiben separat begrenzt.

Die Konstruktionen stehen im separaten Werkzeug `curve_checker_cases.py`.
Es importiert weder Konverter noch Prüfer. Die Annotationen entstehen aus
expliziter Geometrie, nicht aus analysierten Konverterausgaben. Drei
Kurvenkonstruktionen mit geradem Anschluss, zusätzlichem gedrehtem
Ellipsenbogen und vollständig verdeckter Kurve werden in je fünf
Ähnlichkeitstransformationen geprüft. Das sind drei synthetische
Konstruktionen, keine 15 unabhängigen realen Familien.

## Nachweise und produktive Voruntersuchung

| Prüfung | Ergebnis |
| --- | ---: |
| Vollständige synthetische native Inventare und Relationen | 15/15 |
| Beschädigte Gegenproben zurückgewiesen | 285/285 |
| Davon unter beiden Renderern pixelgleich | 45/45 |
| Bestehender Gruppengenerator: untersuchte synthetische Eingaben | 15 |
| Bestehender Gruppengenerator: erzeugte Vorschläge | 0 |

Die 19 Fehlerarten je Szene umfassen fehlende/doppelte Kurven, verdeckte
Inventarfehler, andere Kontrollpunkte, unterbrochene Verbindungen, falsche
Tangenten, Farbe, Breite, Transformation, Tiefe, Bogenrichtung, Bogenast,
Achsrotation und Radius sowie nicht unterstützte Füllung, zusammengesetzte
Pfade und transparente Deckobjekte. Separate Regressionen isolieren
Anschluss- und Tangentenfehler innerhalb der allgemeinen Objekttoleranz.

Nach dem separaten Freeze wurde `group_proposals` auf allen 15
synthetischen Rasterbildern mit fünf Sekunden und höchstens 32 Vorschlägen
untersucht. Es entstehen keine Gruppenvorschläge. Die Quellprüfung erklärt
diesen Befund: Der Generator erzeugt derzeit nur Schaft-/Dreiecksgruppen
und gekreuzte Rechteck-/Gelenkgruppen. `part_regions` behandelt keine
Kurvenpfade, und die produktive Verbindungsprüfung kennt nur diese beiden
Gruppen. Ein bloßes Hinzufügen eines `path` würde daher keine vollständige
lokale Kurven-/Anschlussprüfung schaffen. Diese Untersuchung ist keine
vollständige CLI-Konvertierung und belegt keinen Kataloggewinn.

[Freeze, Rendererbefunde und Reproduktion](../artifacts/evaluation/curve_checker_v1/README.md).
798 gezielte Regressionen sowie 42 Kerntests bestehen ohne Überspringungen.
CI ist um den separaten Kurvenprüfer und den Zwei-Renderer-Replay ergänzt;
ein GitHub-Lauf wurde nicht gestartet.

## Grenzen und nächstes Arbeitspaket

Zusammengesetzte oder geschlossene Kurvenpfade, implizite Fortsetzungen,
Aufteilung in Teilkurven, Gradwechsel zwischen Q und C, Schleifen mit
identischen Endpunkten, Kurvenschnittpunkte, gefüllte Kurven, Strichelung,
Marker, CSS, Transparenz, Effekte und affine Scherung benötigen einen
separaten Vertrag. Unbekannte Semantik wird zurückgewiesen.

Verdeckte Geometrie muss hier vollständig vorhanden sein. Das positive
`hidden_geometry_verified` bezeichnet die Übereinstimmung mit der bekannten
synthetischen Konstruktion; es behauptet keine Rekonstruktion aus verdeckten
Realbildpixeln. Eine Auslassung verdeckter Kurven wird nicht akzeptiert.
Die alten Prüfer bleiben für ihre bisherigen Verträge zuständig.

**FALLBACK-GROUPS-CURVE-PROPOSALS-08** folgt als begrenztes produktives
Entwicklungspaket: Zunächst beobachtbare offene Kurven-/Anschlussgruppen
ohne verdeckte Ergänzungen aus Rasterbelegen vorschlagen. Echte Kurvenregionen,
Anschlüsse, unveränderte Bildgates und unabhängigen Inventarvertrag gemeinsam
prüfen. Vorher/nachher identische Eingaben, Budgets und Seeds verwenden;
verdeckte Stücke nicht aus den synthetischen Annotationen übernehmen.

Menschlicher Annotationsaudit, breite reale Vollständigkeitsabnahme,
SEARCH-STRUCTURE-01 und SEMANTIC-COMPLETENESS-02 bleiben offen.
HC0010, Rail, AC5041 und AC5050 bleiben `sealed_unrun`.
Null Reserveversuche, null Modellfreigaben, keine Archivpromotion.
