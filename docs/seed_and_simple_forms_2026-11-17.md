# Seeds, Vorlagenzeit und einfache Formen

Die Korrektur vom 17. November betrifft die gemeinsame Suche für alle
Bildnamen. Vorher wurde der GUI-Seed im Vorlagenprozess nicht übergeben;
dessen Fortsetzung verwendete dadurch Seed 0. Zudem bestanden Objektänderungen
überwiegend aus derselben festen Liste, und bereits ein knapp bestandener
Rastervergleich konnte die Vorlagensuche nach einer Prüfung beenden.

## Seed und Nachweis echter Sucharbeit

Der Seed wird an CLI, Vorlagenprozess und Nachbesserung übergeben und im Bericht
als vollständiger 64-Bit-Wert gespeichert. Er bestimmt frühe Parameterreihenfolgen,
Objektauswahl, Reihenfolge und zusätzliche multiskalige Bewegungs- und
Grössenvorschläge sowie die Auswahl plausibler alternativer Suchäste. Die
Zufallsfolgen sind aus Seed und Kandidateninhalt abgeleitet und unabhängig vom
globalen Zufallszustand und dem Dateinamen.

`render_sequence_sha256` protokolliert ausschliesslich die tatsächlich neu
angeforderten Renderkandidaten und das zugehörige Rasteroriginal. Der Seed selbst
geht nicht in diesen Hash ein. Ein anderer Hash beweist damit andere Sucharbeit;
eine andere Seed-Beschriftung allein genügt nicht. Gleiche Seeds reproduzieren
dieselben Vorschlagsfolgen bei gleichem Eingang und gleichem Arbeitsumfang.
Ein Zeitlimit kann je nach Laufzeit unterschiedlich weit in dieser Folge enden.
Gute Endergebnisse dürfen auch mit unterschiedlichen Seeds identisch sein.

## Gleiche Intensität bei Vorlagen

Die Vorlage erhält die volle maximale Profilzeit: 45, 120 oder 240 Sekunden.
Die gemeinsame Ausrichtung ist nur der erste Abschnitt. Ein bestandener
allgemeiner Rastertest beendet die weitere Suche nicht, wenn das strengere
Suchziel noch offen ist oder eine einfachere native Darstellung geprüft werden
kann. Die pauschale Begrenzung auf 48 Konstruktionsrunden entfällt; Zeitbudget,
erreichtes Suchziel und tatsächlich erschöpfte neue Vorschläge bleiben Grenzen.
Die bildbezogenen Wiederholungssperren und Parameterbudgets bleiben erhalten.

Ein absolutes Ende berücksichtigt den Interpreterstart. Native Verbesserungen
werden schon während der Suche atomar als SVG und Bericht gesichert. Wird der
Worker beendet, prüft die GUI den vorhandenen Stand erneut am Original und an
der Beschreibung. Eine beendete Suche verliert ihren besten gültigen Stand nicht
an einen letzten schlechteren Versuch. Schutzverletzende Vorschläge dürfen auch
über die Nebenweg-Auswahl nicht übernommen werden.

Die laufende Vorschau und ihr Versuchsprotokoll verwenden ebenfalls die gemeinsame
Bewertung von Konturen, Vordergrund und Darstellungskomplexität. Ein kleinerer
globaler Pixelfehler friert die Anzeige nicht mehr ein. Die Beschreibung wird
dabei, soweit prüfbar, berücksichtigt. Reine Kontrollrenderings bereits bekannter
Kandidaten werden aus dem bildbezogenen Cache bedient.

## Einfachheit für alle Formen

Jeder native Kandidat erhält zusätzlich zur bisherigen Bildbewertung eine
Darstellungskomplexität. Sie berücksichtigt die Zahl der zeichnenden Elemente,
ihre geometrischen Koordinaten und allgemeine Pfadkodierungen. Die Zusatzkosten
betragen `0.00005` je Element, `0.000002` je Koordinate und `0.000005` je allgemeinem
Pfad beziehungsweise Polyline. Das gilt für alle Formklassen; die bestehenden
absoluten Raster- und Beschreibungsprüfungen bleiben verbindlich.

Die gemeinsame Suche kann redundante Punkte entfernen, zusammengehörige
gleichfarbige Fragmente zu einer ganzen Form konsolidieren und Pfade oder
Polygone durch native Geraden, Rechtecke, Dreiecke, Kreise und Ellipsen ersetzen.
Jeder Ersatz wird gegen das Original gerendert. Eine gleich aussehende, einfachere
Darstellung zählt ebenfalls als Fortschritt. Eine geringere Elementzahl allein
rechtfertigt weder fehlende Bildteile noch ein schlechteres gültiges Ergebnis.

Klar angegebene Anzahlen einfacher Formen werden in logische Objektgrenzen
übersetzt. Das umfasst auch übliche Angaben ohne das bisher nötige Wort
„genau“, beispielsweise „eine Gerade“, „ein Kreis“ oder „drei horizontale Linien“.
Eine geknickte Polyline zählt nicht als eine Gerade. Vollständige einfache
Aufzählungen begrenzen auch zusätzliche ungenannte Objekte. Ein bereits
zerstückelter Eingang darf schrittweise repariert werden, wenn die Überzahl und
die Komplexität sinken; ein solcher Zwischenstand besteht dadurch noch keine
Abnahme. Randkonturen und ausgesparte Streifen werden, soweit geometrisch
nachweisbar, dem zugehörigen Objekt zugeordnet.

Die Sprachprüfung bleibt auf diese prüfbaren Angaben begrenzt. Referenzen auf
Unterteile komplexer Kompositionen sind keine pauschale Zählung sämtlicher
SVG-Striche. Eine weltweite mathematische Minimalität oder das vollständige
Verstehen beliebigen Freitexts wird nicht behauptet.

## Regressionen

`test_seed_search_effect.py` prüft echte Kandidatenänderungen, reproduzierbare
begrenzte Suchläufe, Seed-Weitergabe über den GUI-Prozess und Ergebnissicherung
bei Unterbrechung. `test_simple_form_representation.py` prüft die Vereinfachung
aller genannten Grundformen, echte Fragmentgruppen, unzulässige Stückelung und
mehrstufige Reparatur. Die bisherigen Such-, Sprach-, Vorlagen-, Renderer- und
Plan-B-Regressionen werden zusätzlich ausgeführt.
