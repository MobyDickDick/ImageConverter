# FALLBACK-GROUPS-CHECKER-05: Segmentdarstellungen unabhängig prüfen

Am 13.11.2026 als begrenztes synthetisches Prüferpaket abgeschlossen.
Der neue Prüfer ordnet mehrere sichtbare Geradenstücke einem vollständig
annotierten logischen Linienobjekt zu. Eine zulässige Gelenkteilung wird
von fehlenden Armen, sichtbaren Anschlusslücken und zusätzlichen Strichen
unterschieden. Der produktive Konverter und seine Qualitätsgrenzen bleiben
unverändert. Dieses Paket erhöht die nachgewiesene Katalogabdeckung nicht.

## Vertrag und Unabhängigkeit

`tools.check_segment_scene` verwendet ausschließlich den unabhängigen nativen
Parser und die unabhängigen Geometrie-/Relationsoperationen von CHECKER-04.
Der damalige Code und Freeze bleiben bytegleich. Keine Runtime-Detektoren,
Gruppenmarkierungen, Modellfreigaben oder Runtime-Anschlussprüfungen fließen ein.
Beliebige IDs und `data-*`-Rollen ändern den Entscheid nicht.

Die externe Annotation verwendet `independent_segment_scene_v1`. Standardmäßig
bleibt jede erwartete Form ein einzelnes natives Element. Nur ausdrücklich
markierte Linien erlauben höchstens acht kollineare Segmente. Eine begrenzte
injektive Mengenzuordnung verbraucht jedes native SVG-Element genau einmal;
überzählige und doppelte Striche werden nicht verworfen. Alternative Zuordnungen
dürfen weder Elemente teilen noch vorhandene Farben-/Strichbreitengrenzen umgehen.

Äußere Endpunkte folgen weiterhin der bisherigen Positionstoleranz von maximal
zwei Pixeln. Zusätzlich begrenzt der Darstellungsvertrag die Kollinearität auf
höchstens 0,25 Pixel und sichtbare Stoßabstände auf höchstens 0,1 Pixel; die
Studie verwendet 0,1 bzw. 0,05 Pixel. Überlappende Mittelliniensegmente sind
ausgeschlossen, auch wenn ein Gelenk sie verdeckt. Zulässige größere Lücken
müssen vollständig innerhalb der tatsächlichen deckenden Füllung explizit
benannter und unabhängig zugeordneter Kreis-/Rechteckobjekte liegen.
Konturbreite wird nicht als deckende Füllung mitgezählt. Jedes Teilsegment
muss hinter dem betreffenden Deckobjekt liegen. Anschlüsse und Kreuzungen
werden an den logischen äußeren Endpunkten und Geraden eigenständig geprüft.

Das bestätigt die zulässige sichtbare Repräsentation, **keine vorhandene
verdeckte Geometrie**: Werden Zwischenstücke ausgelassen, nennt der Bericht
die betroffenen Objekte unter `omitted_hidden_geometry` und setzt
`hidden_geometry_verified=false`. Ein negativer oder nicht unterstützter
Entscheid behauptet ebenfalls keine positive Prüfung verdeckter Geometrie.
Bekannte vollständig verdeckte eigene Objekte bleiben Inventarpflicht.
Für reale verdeckte Formen sind Herkunft und Unsicherheit weiterhin zu annotieren.

Grenzen: 512 Pixel je Seite, 48 native Elemente, 24 Verschachtelungen,
4.096 gemeinsame Enumerations-/Zuordnungsschritte, 256 Darstellungsalternativen
je logischer Linie. Budgetüberschreitung und nicht unterstützte Semantik
erhalten keine Freigabe. Zulässig sind hier nur gerade Segmente mit stumpfen
Endkappen; beliebige Kurven, Konturzerlegung, transparente Deckflächen,
Scherungen, ungleichmäßige Skalierung und allgemeine SVG-Äquivalenz fehlen.

## Entwicklung und Gegenproben

Die externen Annotationen der vorherigen versiegelten synthetischen Konstruktion
werden mit expliziten Darstellungsrechten weiterverwendet. XML-Teilungen sind
separat mit festen Konstruktionskoordinaten formuliert. Fünf Transformationen
prüfen jeweils eine vollständige Linie, ein unter dem Gelenk geteiltes Gestänge
und mehrere Teilungen einschließlich eines sichtbaren Stoßes sowie einer
ausgelassenen Teilstrecke unter einem Rechteck. Das ist **eine Konstruktion
mit Transformations- und Darstellungsvarianten**, keine neue reale Kohorte.

| Prüfung | Ergebnis |
| --- | ---: |
| Vollständige logische synthetische Inventare | 15/15 |
| Eigenständige Negativkontrollen | 255/255 abgelehnt |
| Davon mit MuPDF und librsvg rasteridentische verdeckte Fehler | 45/45 trotzdem abgelehnt |
| Historische synthetische Zielkonstruktionen | 6/6 |
| Historische direkte Entwicklungsausgaben | 0/18 vollständig zertifiziert |

Die 17 Gegenproben je Darstellung entfernen einzelne Segmente, Kontext,
Pfeilkopf, Gelenk oder bekannte verdeckte Objekte. Weitere Kontrollen ergänzen
doppelte, parallele, konturfolgende oder verdeckte Zusatzstriche und verändern
Anschlüsse, Strichstil, Farbe, Deckung, Transformation oder Reihenfolge.
Zusätzliche Regressionen prüfen echte Deckgeometrie statt erwarteter Masken,
versetzte/überlappende Segmente, umgekehrte Endpunkte und beide Suchgrenzen.
Die Positivszenen benötigen höchstens 75 gemeinsame Arbeitsschritte.
Rasterdiagnosen ändern den geometrischen Entscheid nicht; eine exakte
Pixelidentität jeder zulässigen Segmentdarstellung wird nicht behauptet.

Alle 18 früheren Ausgaben besitzen nun passende Segmentoptionen für das Gestänge
und keine fehlenden logischen Objektkandidaten. Trotzdem bleiben jeweils drei
bis sechs native Striche unzugeordnet. Die damaligen sechs Ausgaben mit je
drei Seeds sind weiterhin keine 18 unabhängigen Fälle. Der neue Vertrag erlaubt
keine zusätzliche Konturzerlegung; diese Striche werden deshalb nicht heimlich
als gleichwertig deklariert. Das ist keine vollständige fachliche Klassifikation
ihrer sichtbaren Bildwirkung. Kein alter Entwurf wird automatisch promoviert.

## Freeze, Prüfung und Folgearbeit

[Separate Evidenz und Reproduktion](../artifacts/evaluation/segment_checker_v1/README.md).
Beide Prüfer, der Evaluator und sämtliche positiven/negativen XMLs samt
Annotationen sind vor jeder Reserveprüfung SHA-256-gebunden. Der Replay prüft
ausgeführten Code und gespeicherte historische SVG-Bytes. Eine zunächst
fehlgeschlagene Vorbereitung mit XML-Namensraumpräfix wurde lokal unter
`.tmp/segment-checker-prefixed-failure` erhalten; MuPDF konnte diese Serialisierung
nicht rendern. Der endgültige unabhängige Freeze verwendet die explizite
SVG-Standardnamensraumserialisierung. Keine Reserve war beteiligt.

477 gezielte Prüfer-/Struktur-/Reserveregressionen sowie 42 Kerntests bestehen
ohne Überspringungen. Der separate Replay besteht mit beiden Renderern.
CI wurde ergänzt; kein GitHub-Lauf gestartet. Keine neue Konvertierung oder
Archiv-Neukonvertierung für dieses Prüferpaket.

Nächstes P0-Paket ist **FALLBACK-GROUPS-CLEANUP-06**: Die im realen Fallback
entstehenden zusätzlichen Restbildstriche anhand des jetzt getrennt
eingefrorenen Inventarvertrags untersuchen. Eine allgemeine saubere
Gruppenkonstruktion muss ohne unbelegte Überzeichnung auskommen oder eine
vorab begründete zusätzliche Konturdarstellung separat annotieren und prüfen.
Vorher/nachher dieselben Entwicklungsraster, Beschreibungen, Budgets und Seeds
verwenden; Originaldetails, richtige Kontextobjekte und negative Kontrollen
erhalten. Keinen nur für höhere Abnahmezahlen gelockerten Prüfer einsetzen.

Danach bleiben Kurven-/Rundungs-/Schattierungsabdeckung, der unabhängige
menschliche Annotationsaudit und reale Vollständigkeitsabnahme erforderlich.
HC0010, Rail, AC5041 und AC5050 bleiben `sealed_unrun`: null reservierte
Versuche, null Modellfreigaben. SEARCH-STRUCTURE-01, GENERAL-SCENE-REAL-05
und SEMANTIC-COMPLETENESS-02 bleiben offen.
