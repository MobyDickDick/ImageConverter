# Neue geometrische Klassenbildung für den vollständigen Katalog

Die bisherige Liste „Nicht konvertierbare Klassen“ enthielt acht Bildnummern
aus einem alten Unterordner. Sie war keine geometrische Taxonomie und keine
aktuelle Prüfung der grundsätzlich vorhandenen Konvertierungsverfahren.

Die neue [Gesamtliste](../artifacts/catalog_classes/index.html) erfasst alle
**1.787 Katalogbitmaps**. **1.781** erhalten eine geometrische Klasse, sechs
reservierte Prüfbilder behalten ihren eigenen Sperrstatus. **Alle 1.781
freigegebenen Bilder sind jetzt einzeln am Original geprüft und zugeordnet.**
Auf die ersten 234 Sichtzuordnungen folgte die Prüfung der restlichen 1.547
Bilder auf 13 nummerierten Kontaktbögen. Größenvarianten wurden einzeln geprüft.
Es bleiben **keine bloßen Beschreibungsvorschläge** für den aktuellen Bestand.
Der Prüfer ist Codex; eine menschliche fachliche Freigabe ist damit nicht behauptet.

## Ergebnis und Bedeutung für die Konvertierbarkeit

**1.756 Bilder** liegen in 15 geometrischen Klassen, für die native Verfahren
oder Teilmodelle im Projekt vorhanden sind. **25** liegen in einer weiteren
Klasse für Fotos, dichte Darstellungen und organische Motive. Die vollständige
[Klassenbilanz](../artifacts/catalog_classes/README.md) nennt alle Anzahlen.

Die Sichtprüfung ändert **586 Klassenzuordnungen** gegenüber der vorherigen
Liste. Der [Änderungsexport](../artifacts/catalog_classes/review_changes.csv)
führt jede betroffene Datei mit alter und neuer Klasse auf. Beispiele:

- `AC0201.jpg` zeigt einen Kreis mit zwei zusammenlaufenden Sehnen;
  `AC0201_L.jpg` zeigt zwei Ventilflügel mit Kreisstellglied. Die ähnlich
  benannten Dateien gehören deshalb zu verschiedenen geometrischen Klassen.
- `GE0021_M.jpg` und `GE0021_S.jpg` sind schlichte Kreishintergründe;
  `GE0021.jpg` enthält einen gefüllten Pfeil im Kreis.
- `GE0301_M.jpg` zeigt Werkzeuge mit Wellen, während `GE0301.jpg` eine
  Flagge im Kreis zeigt. Die Referenzbeschreibung war als Klassenquelle ungeeignet.
- Gerade Verlaufsbänder, Pfeile mit Dreiecksspitzen, Schäfte mit offenem
  Bogenanschluss, T-Verzweigungen und Viertelkreis-Rohrbögen werden getrennt
  als Unterformen dokumentiert.

Damit ist eine breite geometrische Einteilung möglich. Die weitergehende
Vermutung, dass bis auf sehr komplexe Bilder bereits alle vollständig
konvertiert werden können, lässt sich aus dem aktuellen Stand jedoch nicht
bestätigen. Eine Klasse mit vorhandenem Teilmodell kann Bilder außerhalb des
konkreten Modellvertrags enthalten. Beispiele sind freie Kurven, Ellipsen,
Textvarianten, zusätzliche Gelenke und neue Kombinationen vorhandener Formen.
Jede Klasse führt daher ihre tatsächlichen Implementierungen und deren
Grenzen auf. Keine Mitgliedschaft setzt den Konvertierungserfolg auf wahr.

Die bisherigen strengen Rasterpässe bleiben **348**, das historische Archiv
bleibt bei **379**. Dies sind überlappende Nachweise mit unterschiedlicher
Abnahme, keine zusätzlichen Erfolge dieser Klassenbildung. Es wurde kein neuer
Konvertierungsbenchmark durchgeführt. Fehlende oder schlechte gespeicherte
SVGs gelten weiterhin nicht als Beweis grundsätzlicher Nichtkonvertierbarkeit.

## Bisher verdeckte Lücken

- **189 Platzhalterbeschreibungen:** Die generische Liste
  „Kreis/Ellipse/Rechteck/Polygon“ benennt mögliche Beschreibungsbausteine;
  sie beschreibt nicht den tatsächlichen Bildaufbau. Die nicht reservierten
  Bilder darunter wurden visuell zugeordnet. Darunter sind einfache Lux-/Q-/V-
  Messkreise, Verlaufsrechtecke und Ventile. Die eigentlichen
  Konvertierungsbeschreibungen müssen weiterhin konkretisiert werden.
- **Eine fehlende Beschreibung:** Das vorhandene `AC0100_from_sample.jpg`
  wird als Panel mit Innenzeichen eingeordnet. Es entsteht dadurch kein
  zusätzlicher Nachweis einer autonomen Konvertierung.
- **135 referenzartige oder vage Texte:** Die endgültigen Sichtzuordnungen
  benötigen keine Referenzauflösung. Falsche und selbstreferenzierende Verweise
  bleiben ein Beschreibungsproblem für die Konvertierung. Die Zahl bedeutet
  nicht, dass alle 135 Referenzen kaputt sind.
- **Beschreibungs-/Bildabweichungen:** Sichtzuordnungen können einer
  Beschreibung widersprechen, beispielsweise bei einem schlichten
  Kreishintergrund statt des genannten Pfeils. Die Zuordnung ändert weder
  den Beschreibungstext noch die Konvertierungsparameter stillschweigend.

## Benutzung und Wiederholung

Im lokalen Webserver unter **Konvertierungsqualität** stehen nun ein Filter
**Geometrische Klasse**, die Zuordnungsbasis und die vorhandenen Modelle mit
ihren Grenzen. Die Klassensuche lässt sich mit Dateisuche, Qualität und
Archivstatus kombinieren. Die beobachteten Formen und Anbauten stehen direkt
bei der jeweiligen Sichtzuordnung. CSV und JSON enthalten die Zuordnung,
Unterklasse und Beobachtung ebenfalls.
Bei einem bereits laufenden Server ist nach dem Codeupdate ein Neustart nötig.

Die separate Liste lässt sich ohne neue Konvertierung oder Rastermessung neu
erstellen:

```powershell
.venv/Scripts/python.exe -m tools.build_catalog_classes
```

Sie verwendet aktuelle Quellbilder und Beschreibungen. Qualitätswerte werden
nur bei passenden Bildbytes und unverändertem Beschreibungstext aus dem
vorhandenen Inventursnapshot übernommen. Geänderte Bildbytes verwerfen bei der
nächsten Erstellung die entsprechende Sichtzuordnung. Eine reine Textkorrektur
behält die unabhängig am Bild geprüfte Klasse. Der ursprüngliche
Beschreibungshash bleibt als Herkunft dokumentiert. Die Zuordnungen stehen in
`config/catalog_class_visual_review.json`. Diese Datei ist reine
Katalogdokumentation und wird nicht für die Konvertierungsentscheidung genutzt.

Die Ergänzungsprüfung ist in
`config/catalog_class_review_decisions.json` mit Zellnummern, Klassen,
Unterformen und Beobachtungen festgehalten. Das
[eingefrorene Bogenmanifest](../artifacts/catalog_classes/review_manifest.json)
bindet jede Zelle an ihre Quelldatei und Prüfsumme. Die Kontaktbögen lassen sich
aus unveränderten Bildbytes wiederherstellen:

```powershell
.venv/Scripts/python.exe -m tools.prepare_catalog_class_review --replay-manifest artifacts/catalog_classes/review_manifest.json --output .tmp/class-review-replay
```

Alle 13 wiederhergestellten Bögen stimmen bytegenau mit den geprüften Bögen
überein. Die [Prüfbilanz](../artifacts/catalog_classes/review_summary.json)
nennt Vollständigkeit, Änderungen und die gesondert erhaltenen Reservierungen.

## Prüfung

43 gezielte Tests für Klassifikation, Inventur, statische Ausgabe,
Katalogexport und Webserver bestehen. Die zwei Tests für lokale
HTTP-Verbindungen und das Beenden eigener Testprozesse wurden außerhalb der
Sandbox ausgeführt. Neue Tests prüfen lückenlose Zellzuordnungen,
Mehrfachzuordnungen, veränderte Quellen, neue Sperren und die Reproduzierbarkeit
der Kontaktbögen. JavaScript-Syntax und `git diff --check` sind fehlerfrei.
Die Browserprüfung bestätigt den kombinierten Klassen-/Dateifilter für die
drei `AC0911`-Größen und sechs reservierte Einträge ohne Bildvorschau.

Der sinnvollste Folgeauftrag ist eine repräsentative echte Konvertierung pro
geometrischer Unterklasse, jeweils mit konkreter Beschreibung und vollständiger
Abnahme. Das liefert eine belastbare Grenze zwischen passendem vorhandenem
Modell, Beschreibungslücke und noch fehlender Komposition.
