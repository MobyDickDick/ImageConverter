# Plan B: falsche PASS-Wertungen und deformierte Kreuz-/Plus-/Minusbilder

Untersucht wurde der neue Export
`C:\Users\marku\Desktop\Temp\plan-b-workbench.zip` mit Seed **34** und
Quelle `AC0130.svg`. Er enthält 16 abgeschlossene Fälle und einen begonnenen
17. Fall. Die bisherige Prüfung meldete 15 Fälle als bestanden.

## Tatsächliche Ursachen

Die Beschreibung enthält „an den Rechteckgrenzen **beschnittenes**
Andreaskreuz“. Der vorhandene Raster-Fitter für genau diese Struktur kannte
„abgeschnitten“ und „begrenzt“, aber „beschnitten“ nicht. Er wurde deshalb
übersprungen. Die allgemeine native Suche erzeugte stattdessen zahlreiche
kurze und teilweise übermalte Striche: beim Original 17 Linien statt zwei
vollständiger Diagonalbänder und dreier zusammengehörender Symbolrechtecke.

Die zweite Ursache lag in der Abnahme. Die Workbench verglich globale
Pixelwerte, Kanten und Vordergrundüberdeckung. Diese Werte konnten trotz
beschädigter Zeichen und zusätzlicher Striche die Grenzen bestehen. Explizite
Beschreibungsbedingungen wurden im übergeordneten Ergebnisvergleich zudem
nur beim Timeout-Pfad erneut geprüft. Ein früher globaler PASS konnte dadurch
die spätere Strukturprüfung und weitere Suche verhindern.

Die Wortwahl ist jetzt im gemeinsamen Modellvertrag berücksichtigt. Die
vorher unterstützten Formulierungen, einschliesslich symbolisch geschriebener
Zeichen, bleiben erhalten. Kein Dateiname und keine gespeicherte SVG wird
vom Fitter als Vorlage gelesen.

## Ergänzte Ausgabeprüfung

Der abschliessende Workbench-Vergleich prüft Beschreibungsbedingungen jetzt
immer, auch nach regulär beendetem Worker. Für das beschriebene Kreuzpanel
mit übereinanderstehenden Zeichen kommt eine unabhängige native Prüfung hinzu:

- passendes Gehäuse, horizontaler Grauverlauf und umlaufender Rahmen;
- genau zwei vollständige, schmale, konvexe und auf das Gehäuse begrenzte
  Diagonalbänder mit entgegengesetzter Richtung;
- ein Plus aus zwei rechtwinklig überlappenden Balken sowie ein separates
  Minus darunter, mittig und sichtbar oberhalb der Kreuzung;
- keine zusätzlichen, verborgenen oder unbekannten Zeichenbestandteile;
- lokale Pixelvergleiche für beide Diagonalbänder und beide Zeichen, damit
  vorhandene, aber übermalte oder praktisch unsichtbare Elemente nicht genügen.

Der Prüfer benutzt weder Parameter des Fitters noch Gruppennamen, feste
SVG-IDs, Katalogkoordinaten oder die Referenz-SVG. Er unterstützt diese
native Ausgabe aus Rechtecken und begrenzten konvexen Polygonen. Andere
semantisch möglicherweise korrekte Darstellungen, etwa komplexe Pfade oder
transformierte Gruppen, werden von diesem begrenzten Vertrag nicht bestätigt.
Ein nicht verifiziertes Bild erhält dadurch keinen grünen PASS allein wegen
seiner globalen Pixelwerte. Das ist keine allgemeine semantische SVG-Prüfung.

Die bisher eingefrorenen globalen Abnahmegrenzen und Zeitlimits sind
unverändert. Auch die Wiederherstellung benutzt die ergänzte Prüfung, wenn
sie entscheidet, ob eine Ausgabe bereits vollständig genug ist.

## Frischer Lauf auf allen 17 Fällen

Mit derselben Quelle, derselben Beschreibung und Seed 34 wurde der reguläre,
SVG-Zugriffe überwachende Workbench-Worker erneut ausgeführt. Die Hashes aller
17 Eingaberaster stimmen mit dem Nutzerexport überein. Es gab keine
Referenz-SVG-Zugriffe des Konverters. Die neuen Vektoren enthalten die
beschriebene Struktur, statt die alten Ausgaben als Vorlage zu verwenden.

**Alle 17 Fälle bestehen** die unveränderten globalen und die zusätzlichen
Strukturprüfungen. Der Lauf benötigte insgesamt 81,42 Sekunden; pro Fall
2,484 bis 33,094 Sekunden bei unverändert 60 Sekunden Gesamtlimit.

| MuPDF-Messung | Alter Export | Korrigierter Lauf |
| --- | ---: | ---: |
| Original: normalisierter Pixelfehler | 0,003702 | 0,000084 |
| Original: Kantenübereinstimmung | 0,86623 | 0,98742 |
| Original: Vordergrund-IoU | 0,85330 | 0,99647 |
| Schlechtester Pixelfehler aller neuen Fälle | — | 0,000482 |
| Kleinster Kantenwert aller neuen Fälle | — | 0,90145 |
| Kleinste Vordergrund-IoU aller neuen Fälle | — | 0,96869 |

Alle 17 gespeicherten Ausgaben wurden ausserdem mit dem unabhängigen
librsvg-Renderer geprüft: **34 von 34 Renderer-/Strukturprüfungen bestehen**.
Die Übersicht aller Originale, Ausgaben und Differenzbilder wurde visuell
kontrolliert. Kein früher grüner Exportfall besteht die neue native
Strukturprüfung; insgesamt werden alle 16 abgeschlossenen alten Ausgaben
nicht bestätigt.

Eine separate, nachgeprüfte Kopie liegt in der tatsächlichen GUI-Workbench
unter der ID `ce97132f276348c18a229dfc6fc24d3b`. Die alten Jobs und Exporte
bleiben unverändert. Die Kopie enthält unveränderte generierte Vektorbytes,
zusätzliche Renderer-Nachweise und den ursprünglichen Kommando-/Laufnachweis.
Das neue ZIP ist ebenfalls lokal verfügbar.

## Farbregel zurückgenommen

Der zuvor eingeführte Schutz gegen jede Aufhellung kleiner dunkler Zeichen
war zu pauschal. Sowohl die Sperre im Vorlagenfitter als auch der pauschale
Helligkeitsmalus beim Speichern sind entfernt. Massstab sind wieder die
Rasterpixel und sichtbaren Konturen, nicht ein festgehaltener Vorlagenton.
Eine neutrale Kompatibilitätsfunktion hält bereits laufende ältere GUI-
Prozesse bis zum Neustart importfähig.

Eine unabhängige kleine Zeichenprobe prüft beide Richtungen: Aufhellen von
`#696969` auf `#a9a9a9` und Abdunkeln in Gegenrichtung, wenn das jeweilige
Rasterziel diese Werte tatsächlich vorgibt. Beide Proben müssen den
Pixelfehler praktisch auf null reduzieren. Die 17 korrigierten Plan-B-
Ausgaben erhalten ihre Zeichenfarben aus ihren jeweiligen Eingaberastern.

## Regressionen und Grenzen

111 gezielte Sprach-/Workbench-/Farbanpassungsprüfungen bestanden im ersten
Lauf. Nach den zusätzlichen Kontrollen gegen verdeckte Diagonalen bestanden
50 gezielte Prüfungen mit allen 17 Varianten und weiteren Gegenproben;
13 reine Prüfer-/Fehlpasskontrollen wurden zusätzlich wiederholt.

Die ältere Kreuzpanel-Suite ergab 104 bestandene Fälle und einen schwankenden
22×42-Kleinstbildfall mit einem harten Zehn-Sekunden-Budget. Seine isolierte
Wiederholung bestand unverändert. Ein Vergleich mit dem unveränderten
HEAD-Modell reproduzierte ebenfalls einen fehlgeschlagenen Fit in diesem
engen Budget. Die Grenzen wurden dafür nicht gelockert. Dieser separate
Kleinstbild-/Zeitbudgetrandfall ist nicht Teil des Nutzerexports mit Breiten
40 bis 44 Pixeln; er bleibt eine bekannte Begrenzung.

Die Abnahme gilt für die 17 Fälle dieses Exports und die genannten
Regressionen, nicht für sämtliche Plan-B-Familien oder beliebige SVG-Syntax.
Alte gespeicherte PASS-Felder bleiben historischer Stand; für neue Versuche
den Webserver nach Ende aktiver Jobs neu starten und die neue Abnahme nutzen.

[Vergleichsübersicht, korrigiertes ZIP und Berichte](../artifacts/evaluation/crossed_panel_workbench_2026-11-16/README.md).
