# FALLBACK-STRUCTURE-01: Mehr native Konstruktionen im tatsächlich benutzten Fallback

Am 12.11.2026 als begrenztes Entwicklungspaket abgeschlossen. Der bisherige
`native_svg_continuation` verändert weiterhin die Parameter vorhandener SVGs;
davor untersucht er jetzt zusätzlich andere native Aufbauten. Die übergeordneten
Abnahmen SEARCH-STRUCTURE-01 und GENERAL-SCENE-REAL-05 bleiben offen.

## Umsetzung und untersuchte Hypothesen

Vor der Runtimeänderung wurden vier bekannte Fehler des zweiten Katalogaudits
eingefroren: AC0030_S, AC0303_1_M, AC0504_1M_sia und GE0362. Originalbytes,
Beschreibungen, damalige generierte SVGs, der alte Fortsetzungscode, lokal
fehlende Merkmale, Seeds und Budgets liegen mit Hashes im
[Evidenzpaket](../artifacts/evaluation/fallback_structure_v1/README.md).
Das sind bekannte Entwicklungsfälle, keine neuen unabhängigen Familien.

Hypothese A rekonstruiert vollständige einfache Szenen aus beobachteten
Farbregionen. Kreis und Rechteck sind wechselbare native Grundformen;
einfarbige und zwei axiale Verlaufsmodelle sind eigene Konstruktionen.
Hypothese B ergänzt native Linien aus unerklärten Rasterregionen. Getrennte
positive/negative Restfehler verhindern, dass dunkle Randfehler helle Innenlinien
überdecken. Farbe, antialiasierte Breite und Ausdehnung benötigen Rasterbelege.
Die Kombination prüft Linien sowohl auf dem bisherigen SVG als auch auf der
besten alternativen Konstruktion. Dies vergrößert Objektarten und Objektzahl,
statt allein andere Parameter desselben Rechtecks zu erzeugen.

Wiederverwendet werden die gemeinsame analytische Kreisvermessung, native
Farbausgabe, Registrierung, Portfolio-Bots, Fortschrittsprotokollierung und
aktive Bilddeadline. Der bestehende `edit_proposals`-Vertrag setzt dagegen ein
vollständig bekanntes Eltern-/Kindinventar voraus. Die unklassifizierten
Auditbeschreibungen liefern dieses Inventar nicht; es wird nicht erfunden.
Eine anschließende allgemeine Szenenkomposition ist weiterhin Folgearbeit.

Die zusätzliche Suche ist auf 32 Vorschläge, acht beobachtete Flächen je
Segmentierung, zwölf Linien je Ausgangskonstruktion und 48 sichtbare Elemente
begrenzt. Raster über 512 Pixel Kantenlänge erhalten vorerst nur die vorhandene
Parameterfortsetzung. Es gibt keine Bild-ID-/Familienweiche, kein Laden alter
Referenz-SVGs in der produktiven Konvertierung und keine Konturpfade als Ausgabe.

Jeder Vorschlag protokolliert Herkunft, sichtbares Inventar, globalen Fehler,
lokalen Gewinn, verbesserte Pixelanteile und Ablehnungsgrund. Explizite
Beschreibungszählungen werden vor dem Rendern geprüft. Ein akzeptierter Edit
muss global verbessern und in mindestens 60 Prozent seiner geänderten Pixel
helfen; dies ist ein Suchfilter, keine fachliche Freigabe. Nachfolgende
Parameteränderungen dürfen neu ergänzte Linien lokal nicht wieder verschlechtern;
ansonsten bleibt der bereits gemessene Strukturentwurf erhalten. Herkunft und
Suchbelege gelangen auch in die persistierte `vector_continuation`-Zeile.

## Ergebnis unter gleichen Budgets

Der begrenzte Fortsetzungsvergleich verwendet für jede Methode und jeden Fall
dieselben fünf Sekunden Gesamtbildzeit, höchstens fünf Sekunden, 384 als
Portfolio-Basisbudget und die Seeds 17, 29 und 43. Auch Vorschlagserzeugung und
Rendern zählen gegen diese aktive Deadline. Einzelne native Aufrufe können
sie geringfügig überschreiten; die beobachtete größte Fortsetzungszeit beträgt
5,016 Sekunden. Dies ist keine neue Echtzeitgarantie.

| Bekannter Entwicklungsfall | Bisheriger Fallback: medianer normierter MSE | Kombiniert | Veränderung | Beide lokale Merkmale bestanden |
| --- | ---: | ---: | ---: | ---: |
| AC0030_S | 0,017961 | 0,006002 | −66,6 % | 0/3 |
| AC0303_1_M | 0,039809 | 0,005555 | −86,0 % | 3/3 |
| AC0504_1M_sia | 0,042548 | 0,008412 | −80,2 % | 0/3 |
| GE0362 | 0,031441 | 0,027956 | −11,1 % | 0/3 |

Alle vier Methoden wurden mit jeweils zwölf Versuchen verglichen: bisheriger
Fallback, nur Grundformen, nur Linien und Kombination. Die unveränderten
Pixelgates bestehen **0/12, 0/12, 0/12 und 3/12**. Beim Kreissymbol liefert erst
die Kombination den Kreis mit zwei Innenlinien. Weder eine bessere rote Fläche
allein noch Linien auf dem falschen Rechteck erreichen diese Abnahme.
Pfeilspitzen und die vollständigen zusammengesetzten Symbole fehlen weiterhin.

Zusätzlich wurden acht echte überwachte CLI-Konvertierungen mit neutralen
Dateinamen durchgeführt: viermal ohne und viermal mit Strukturerweiterung,
jeweils Seed 17, acht Sekunden reguläres / zehn Sekunden maximales Bildbudget
und fünf Sekunden Mindestaufwand. Die Initialkonstruktion entsteht hier frisch
aus Original und Beschreibung; die historischen SVGs sind kein Eingang.
Die Pixelpässe steigen von **0/4 auf 1/4**, ebenfalls AC0303_1_M.
Alle acht Ausgaben wurden gespeichert; kein Referenzzugriff wurde gemeldet.
Die äußeren Laufzeiten einschließlich CLI-Prozessstart liegen bei 8,17–8,73
Sekunden. Dieser CLI-Vergleich ist eine Ablation des aktuellen Codes; der
separate Fortsetzungsvergleich verwendet den eingefrorenen alten Code.

## Unabhängige Gegenprüfung und Grenzen

Alle 56 gespeicherten Ausgaben wurden gegen die Originalpixel erneut mit MuPDF
und unabhängig mit librsvg geprüft. Beide bestätigen die oben genannten
Pixelpasszahlen. Die drei kombinierten Kreisfortsetzungen und die frische
CLI-Kreisrekonstruktion bestehen jeweils beide lokal markierten Innenlinien.
16 beschädigte Kontrollen entfernen alle/eine Linie, verschieben eine Linie
oder ersetzen den Kreis durch ein Rechteck. Beide Renderer weisen alle
Kontrollen über globale oder lokale Gates zurück. Acht der 32
Renderer-Kontrollprüfungen würden bei ausschließlicher globaler Pixelprüfung
noch bestehen: Die lokalen Tests sind hier tatsächlich erforderlich.

**Modellfreigaben bleiben 0.** Die Bildbeschreibung des roten Kreises spricht
weiterhin von einem grauen Kompressor. Die neue Suche kann das Raster besser
rekonstruieren, beweist aber weder diesen Beschreibungstext noch die vollständige
Semantik allgemeiner SVGs. Kein Pixelpass wird automatisch validiert, keine
Zeile gelangt dadurch neu ins Archiv zufriedenstellender Konvertierungen.
Raster-/Objekt-/Beschreibungsprüfungen und Prozessaufsicht bleiben erforderlich.

Die zusätzliche Suche erhält kein eigenes Zeitbudget. Das begrenzte Vorziehen
von Strukturvorschlägen reserviert Exploration, bevor die Parametersuche ihre
Zeit verbraucht. Es ist noch kein gemeinsamer Scheduler beliebig vieler
fortsetzbarer Strukturfamilien. Farbsegmentierung und gerade Linien reichen
für zusammengesetzte Werkzeug-/Flammenformen und Pfeilköpfe nicht aus. Größere
Raster und gekrümmte/überdeckte Symbolgruppen sind ebenfalls offene Grenzen.
Die weiterhin gesperrten realen Reserven HC0010/Rail wurden nicht ausgeführt;
es wird keine unabhängige reale Familienabnahme behauptet.

139/139 gezielte Regressionen einschließlich Fortschrittssicherung, Sample-Erhalt
und Archivintegrität bestehen; das Kernprofil besteht 42/42. Die vollständige
Archiv-Neukonvertierung ist ausdrücklich abgewählt und wird nicht als bestanden
gezählt. Bei der Prüfung wurde
eine bereits zuvor fehlschlagende Sample-Regressionsfixture entdeckt: Sie las
eine inzwischen überschriebene Produktions-SVG außerhalb ihres Viewports.
Der Test verwendet jetzt die bytegleiche, durch den ursprünglichen Evidenzhash
bestätigte Nachzeichnung als feste Fixture. Die aktuelle Produktionsdatei und
historische Evidenzen wurden dabei nicht überschrieben. Ein Ubuntu-CI-Job
prüft die Regressionen und die tatsächliche CLI einschließlich unabhängiger
librsvg-Kreis-/Detailprüfung; sein erster GitHub-Lauf steht noch aus.

## Nächstes Paket: FALLBACK-GROUPS-02

Die nächste Erweiterung soll aus Linien wieder überprüfbare Objektgruppen
bilden: Schaft plus dreieckiger Pfeilkopf sowie Quadrat plus Diagonalen,
Anschluss und Gelenk. Mindestens zwei allgemeine Gruppenhypothesen gegen die
jetzige Linienaddition bei unverändertem Gesamtbudget vergleichen. Positive,
fehlende, versetzte und falsch verbundene Teile lokal prüfen. Eine Sammlung
zusätzlicher Einzelstriche allein genügt nicht als Objektfreigabe.

Die vier jetzt bekannten Fälle bleiben Entwicklung. Vor weiteren Änderungen
neue reale Familien mit Originalbytes, Beschreibungen, lokalen Objekt- und
Relationsmarkierungen und Hashes separat einfrieren und sperren. Bekannte
Verbesserungen, synthetische Varianten und neue Familien getrennt ausweisen.
Die allgemeine semantische Abnahme bleibt SEMANTIC-COMPLETENESS-02 zugeordnet.
