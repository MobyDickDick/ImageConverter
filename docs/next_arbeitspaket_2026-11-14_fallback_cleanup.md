# FALLBACK-GROUPS-CLEANUP-06: saubere native Gruppenkonstruktionen

Am 14.11.2026 als begrenztes synthetisches Entwicklungspaket abgeschlossen.
Der produktive Fallback erzeugt auf denselben sechs Entwicklungsszenen mit
denselben drei Seeds jetzt 18/18 vollständige logische Inventare statt 0/18.
Alle 18 Ausgaben bestehen weiterhin die bisherigen globalen und lokalen
Bildgates mit MuPDF und librsvg. Auch die sechs echten CLI-Ausgaben bestehen
beide Renderer und den unveränderten unabhängigen Segment-/Relationsprüfer.
Das ist kein neuer Nachweis realer Katalogabdeckung.

## Zwei Ursachen und ihre Korrektur

Die 18 separat eingefrorenen früheren Ausgaben enthalten insgesamt 66
nicht zugeordnete Linien entlang bereits nativer Rechteckkonturen und sechs
zusätzliche, überdeckte unvollständige Rechtecke. Der Inventarprüfer hatte
damit zusätzliche native Objekte erkannt; aus dem bisherigen Befund allein
war deren sichtbare Bildwirkung noch nicht klassifiziert.

1. Der Restbild-Houghdetektor interpretiert Registrierungs- und
   Antialiasingabweichungen an vorhandenen Konturen als neue Linien.
   Blasse Zusatzstriche verbessern zwar etwas den Pixelwert, entsprechen
   aber keinem zusätzlichen annotierten Objekt. Vor dem Rendern prüft der
   produktive Suchweg nun, ob eine vorgeschlagene Linie eine vorhandene
   native Gruppenkante nachzeichnet: Richtungsabweichung höchstens 0,12
   im Betrag des normierten Kreuzprodukts und mindestens 90 % Längenbelegung
   innerhalb der beiden halben Strichbreiten plus 0,5 Pixel.
   Abgelehnte Vorschläge bleiben mit `existing_group_edge` und tatsächlicher
   Besitzerkante im Bericht sichtbar und verbrauchen das Vorschlagsbudget,
   jedoch keinen Renderaufruf. Farben oder Katalogkennungen begründen diese
   geometrische Zuordnung nicht. Parameterkorrekturen bleiben der vorhandenen
   nativen Nachoptimierung vorbehalten.
2. Ein zuerst geprüfter Add-Vorschlag kann das alte unvollständige Rechteck
   vollständig überdecken. Die anschließend pixelgleiche Ersetzung gewinnt
   dann den strengen Fehlervergleich nicht mehr. Bei räumlicher Überlappung
   wird deshalb zuerst die atomare Ersetzung geprüft, danach weiterhin die
   Ergänzung. Beide benötigen die bisherigen Bild-, Detail-, Beschreibungs-
   und Anschlusstore. Korrekte fremde Kontextobjekte bleiben erhalten.

Die neue Kantenprüfung ist eine begrenzte Vorschlagsfilterung, kein Ersatz
für einen Abnahmeprüfer. Sie unterstützt gerade native Gruppenlinien,
ungerundete Rechteckkonturen und gefüllte Polygonränder in identischen
Viewportkoordinaten. Transformierte, gestylte oder mit Effekten versehene
Teilbäume, Definitionen und abweichende Viewports liefern keine vermuteten
Besitzerkanten. Kreisbögen werden hier nicht als Geradenbesitzer behandelt.
Sehr eng parallele tatsächlich getrennte Striche können innerhalb dieses
Registrierungsbereichs weiter eine andere Strukturhypothese benötigen.
Eine bloße Überschneidung der Gruppenbox unterdrückt keine Linie.

## Vergleich und Gegenproben

Vor der Runtimeänderung wurden die bisherigen Raster, Beschreibungen,
Ausgangs-SVGs, Annotationen, vier Runtimequellen und Prüfsummen separat
gesichert. Fünf Sekunden und höchstens 32 Vorschläge je direktem Versuch,
Portfolioseeds 17/29/43 und die bisherigen CLI-Budgets bleiben unverändert.
Die Prüfer von CHECKER-04/-05 einschließlich ihrer alten Freeze-Dateien
wurden nicht geändert; ihre Integritätsprüfung besteht.

| Prüfung | Bisher | Jetzt |
| --- | ---: | ---: |
| Vollständige unabhängige logische Inventare, direkte Suche | 0/18 | 18/18 |
| Globale/lokale Bild- und Runtime-Anschlussgates, beide Renderer | 18/18 | 18/18 |
| Echte CLI, Bild- und unabhängige Inventar-/Relationsgates | vorher hier nicht neu gemessen | 6/6 |
| Beschädigte Inventarkontrollen | – | 42/42 abgelehnt |

30 Gegenproben entfernen Gruppen, Kontext oder Pfeilköpfe, verändern den
Anschluss oder ergänzen ein fremdes Objekt. Beide Renderer lehnen sie mit
den bisherigen Gates ab. Zwölf weitere Gegenproben ergänzen eine doppelte
Diagonale oder einen Konturstrich: Sie bestehen die Pixelgates, werden aber
vom unabhängigen vollständigen Inventar zurückgewiesen. Diese Kontrollen
bleiben ausdrücklich unzulässig; der Prüfer toleriert Überzeichnung nicht.

Regressionen zeigen, dass eine neue rasterbelegte Linie innerhalb einer
Gruppenbox weiter ergänzt wird. Innenlinien, getrennte parallele Linien,
verlängerte und kreuzende Linien sind keine bloßen Konturduplikate.
Ungeeignete Koordinaten, geerbte Stile, Deckung und Transformationen werden
nicht in passende Geometrie umgedeutet. 557 gezielte Regressionen und 42
Kerntests bestehen ohne Überspringungen. CI wurde um den neuen direkten und
CLI-Nachweis ergänzt; kein GitHub-Lauf gestartet.

Ein erster lokaler Zwischenstand beseitigte die Konturstriche, ließ aber
die überdeckten Rechtecke in zwei Szenen stehen (12/18). Er ist unter
`.tmp/fallback-cleanup-current` erhalten. Der endgültige Stand behebt beide
Ursachen. Frühere Belege wurden nicht überschrieben.

## Grenzen und nächste Arbeit

[Evidenz, Prüfsummen und Reproduktion](../artifacts/evaluation/fallback_cleanup_v1/README.md).
Die sechs Ausgangsszenen variieren Farbe und fehlerhafte Ausgangsobjekte,
nicht sechs unabhängige Topologien. Drei Seeds liefern keine 18 unabhängigen
Familien. Die CLI prüft wiederholte Farbvarianten derselben Anordnung.
Ausgelassene verdeckte Gestängestücke bleiben ausdrücklich
`hidden_geometry_verified=false`; bestätigt wird der annotierte sichtbare
Darstellungsvertrag. Keine Modellfreigabe und keine Archivpromotion.

Als nächstes begrenztes Paket folgt **FALLBACK-GROUPS-CURVES-07** im offenen
SEARCH-STRUCTURE-01: einen separaten unabhängigen Prüfumfang für native
Kurven/Bögen definieren, externe synthetische Konstruktionen und Gegenproben
vor Änderungen einfrieren und fehlende, zusätzliche, falsch verbundene sowie
verdeckt beschädigte Kurven unterscheiden. Bestehende Geradenprüfer und
Rastergates nicht erweitern, um bisherige Fehler nachträglich zu akzeptieren.
Erst danach entsprechende saubere produktive Gruppenvorschläge untersuchen.

Menschlicher Annotationsaudit, breite reale Vollständigkeitsabnahme und
SEMANTIC-COMPLETENESS-02 bleiben offen. HC0010, Rail, AC5041 und AC5050 bleiben
`sealed_unrun`: null reservierte Versuche und null Modellfreigaben.
