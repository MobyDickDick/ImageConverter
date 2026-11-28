# Weiteres Vorgehen nach AP 2

**Stand:** 28. November 2026.

**Entwicklungszweig:** `experimental/explorative-conversion`.

**Vereinbarung:** Der Anwender unterstützt die nachfolgende Reihenfolge.
Die Umsetzung der Etappen steht noch aus; dieser Auftrag dokumentiert das Vorgehen.

Zuerst entstehen eine sichtbare Demo und eine verständliche Architekturübersicht.
Danach werden CI-Fehler nach Ursachen gruppiert und in begrenzten Paketen behoben.
Anschliessend folgen AP 3 und AP 4. Eine vollständige Bereinigung des Altbestands
ist keine Voraussetzung für die Weiterentwicklung des explorativen Kerns.
Der Aufwand soll kontrollierbar bleiben und das Wochenkontingent schonen.

## Ausgangslage und vorhandene Tests

AP 1 stellt den synchronen Konvertierungskern bereit. Seine durch den Anwender
gemeldete Testabnahme unter Windows/Python 3.10.11 umfasst neun bestandene Tests
in 12,25 Sekunden. AP 2 ergänzt frei kombinierbare Grundformen, variable
Objektanzahlen, stabile IDs, Strukturänderungen und Beziehungen.

Die gemeinsame [CI-Abnahme von AP 1 und AP 2](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454068)
für Commit `af518904fe2cb8c9cb4f5c12fa9b0c7c4536c07f` besteht auf Windows und
Ubuntu 24.04 mit Python 3.10.11 jeweils alle 40 Tests. JUnit-Berichte sind am
Lauf verfügbar. Anschauliche Beispiele im Quellcode sind
`test_real_rendering_paint_order_and_all_primitives` und
`test_structural_candidates_compete_and_poor_real_draft_survives` in
[test_exploratory_ap2.py](../../tests/test_exploratory_ap2.py).
Eine betrachtbare Galerie der erzeugten Bilder und SVGs fehlt bisher.

AP 2 ist noch keine automatische Suche über verschiedene Objektstrukturen.
Der derzeitige Standardanbieter liefert im Wesentlichen Rechteck und Ellipse;
`seconds=300` setzt eine Obergrenze. Rasterbasierte Hypothesen entstehen in AP 3,
die eigentliche Struktur- und Parameteroptimierung mit gemeinsamem Budget in AP 4.

Die separate [Repository-CI](https://github.com/MobyDickDick/ImageConverter/actions/runs/46131454133)
war beim Abruf für diese Dokumentation noch nicht abgeschlossen: von 49 Jobs
waren 18 erfolgreich, 20 fehlgeschlagen und 11 laufend. Dieser Zwischenstand
ist keine abschliessende Fehlerliste; ein Job kann mehrere fehlerhafte Tests
enthalten. Vor der Fehlerbereinigung ist der dann aktuelle Endstand zu erfassen.

## Etappe 1 Sichtbare Demo und Architekturübersicht

Ein kleiner, reproduzierbarer GitHub-Actions-Lauf erzeugt einen herunterladbaren
HTML-Bericht mit Originalbild, SVG-Vorschau, Unterschiedsbild und Qualitätswerten.
Er zeigt alle sechs Grundformen, Zeichenreihenfolge sowie Hinzufügen, Entfernen
und Typwechsel von Objekten. Ein unzureichender echter Vektorentwurf bleibt
sichtbar und ist eindeutig als nicht freigegeben gekennzeichnet.
Die Demo unterscheidet vorgegebene Szenenänderungen von selbstständig gefundenen
Verbesserungen; sie darf den Entwicklungsstand nicht überzeichnen.

Eine kurze Architekturübersicht erklärt den Weg eines einzelnen Bildes:
Raster und optionale Beschreibung → Startentwürfe → Rendering und Bewertung →
Szenenänderung → bester Entwurf. Sie benennt den Einstiegspunkt, die beteiligten
Datenobjekte und die Dateien, die der Anwender für eine Änderung benötigt.
Ein kommentiertes Beispiel und eine Anleitung für Breakpoints ergänzen die Übersicht.
Die Demo selbst wird ausschliesslich in GitHub Actions ausgeführt.

**Abnahme:** Der Anwender kann die Ergebnisse ohne eigene Testinstallation
betrachten, den Ablauf im Code wiederfinden und nachvollziehen, wo eine
Grundform, Qualitätsbewertung oder Suchstrategie angepasst wird. Umfang und
Artefakte sind klein genug für eine gezielte Prüfung nach Änderungen.

## Etappe 2 CI nach Ursachen ordnen

Zuerst werden vorhandene Logs und Artefakte ausgewertet. Eine Fehlerliste hält
je Befund betroffenen Commit, Job und Test, Fehlermeldung, Reproduktionsweg,
vermutete oder bestätigte Ursache, Priorität und nächsten Schritt fest.
Gleichartige Fehler werden gruppiert, gemeinsame Ursachen jedoch erst nach
Überprüfung als bestätigt bezeichnet. Der Vergleich mit einem passenden
Ausgangsstand trennt neue Regressionen von bereits vorhandenen Problemen.

Die bisherigen Stichproben zeigen fehlende Worker-Nachweise, fehlende Ausgaben
oder Zeitüberschreitungen, nicht bestandene Qualitätsprüfungen, abweichende
Beschreibungen und widersprüchliche Objektzählungen. Diese Befunde sind noch
keine vollständige Ursachenanalyse. Für Reproduktionen werden zuerst die
kleinsten aussagekräftigen CI-Prüfungen gewählt.

**Abnahme:** Eine priorisierte, nach Ursachen geordnete Liste benennt die
nächsten wenigen Reparaturen, ihre erwartete Wirkung, den Prüfaufwand und die
verbleibende Unsicherheit. Die Diagnose geht nicht unbegrenzt in Reparaturen über.

## Etappe 3 Begrenzte Reparaturpakete

Zuerst werden klar abgegrenzte gemeinsame Ursachen mit hoher Wirkung bearbeitet,
insbesondere technische Ablauf- oder Ausgabeprobleme. Schwierige geometrische
Einzelfälle erhalten einen eigenen Eintrag und verdrängen die Entwicklung des
generischen Suchkerns nicht. Qualitätsgrenzen werden durch eine Reparatur nicht
abgeschwächt, um Prüfungen grün erscheinen zu lassen.

Jedes Paket enthält wenige benannte Ursachen und passende CI-Prüfungen.
Nach einem sinnvollen Paket folgt eine breitere Regression; die vollständige
Katalogbatterie wird nicht nach jeder Kleinigkeit erneut gestartet.
Unveränderte oder neue Fehler bleiben ausdrücklich sichtbar.

**Abnahme je Paket:** Änderungen, überprüfte Wirkung, CI-Links, offene Fehler
und die aktualisierte Restschätzung sind dokumentiert. Der Umfang wird nicht
stillschweigend auf die gesamte Fehlerliste ausgeweitet.

## Aufwand und Schutz des Wochenkontingents

Die folgenden Werte sind grobe Grössenordnungen konzentrierter Entwicklungsarbeit,
keine Zusagen für Agentenlaufzeit oder Verbrauch des Wochenkontingents.

| Umfang | Vorläufige Grössenordnung |
| --- | --- |
| Ursachen gruppieren und Reparaturen priorisieren | Einige Stunden |
| Klar begrenzte gemeinsame Ursachen beheben | Weitere Stunden bis wenige Tage |
| Sämtliche alten Konvertierungs- und Qualitätsfälle zuverlässig bereinigen | Mehrere Tage bis deutlich länger; derzeit schlecht begrenzbar |

Für Demo und Übersicht folgt eine eigene kleine Umfangsschätzung beim Start
von Etappe 1. Ein verbindliches Zahlenbudget wurde noch nicht vereinbart.
Ein seriöser Prozentsatz des Wochenkontingents lässt sich aus diesen Schätzungen
nicht ableiten. Entwicklungsaufwand und CI-Rechenzeit sind getrennt auszuweisen.
Die bestehende vollständige Katalogprüfung hat ein Zeitlimit von 330 Minuten
je Teiljob; das ist ein Höchstwert und keine gemessene Laufzeit.

Vor jeder Etappe wird ihr konkreter Umfang mit einem Aufwandsrahmen festgehalten.
Bei Erreichen dieses Rahmens oder einer wesentlichen Überschreitung der Schätzung
werden Ergebnis und offene Punkte gesichert; die Arbeit wird nicht unbemerkt zu
einer mehrtägigen Gesamtbereinigung ausgedehnt. Kurze gezielte Prüfungen und
wiederverwendbare Evidenz haben Vorrang vor wiederholten vollständigen Läufen.

## Verständlichkeit als Entwicklungsanforderung

Der Bestand unter `src/iCCModules/` umfasst beim Ausgangsstand 244 Python-Dateien;
mehrere Module überschreiten 100 KB. Die fehlende Übersicht muss daher durch
eine einfachere Struktur und klare Abläufe behoben werden.

Der experimentelle Kern wird schrittweise zum verständlichen Hauptweg ausgebaut.
Bewährte mathematische Verfahren bleiben über schmale Adapter nutzbar.
Für die weitere Umsetzung gelten folgende Anforderungen:

- Ein klarer öffentlicher Einstieg und wenige ausdrücklich übergebene Datenobjekte.
- Benannte Zuständigkeiten je Modul und ein nachvollziehbarer Ablauf je Bild.
- Ein synchron verfolgbarer Debugpfad sowie verständliche Fehler mit Kontext.
- Keine neuen versteckten Zustände oder zusätzlichen Wrapper ohne konkreten Nutzen.
- Kommentare und Beispiele erklären Entscheidungen und typische Anpassungsstellen.
- Tatsächliche Vereinfachungen am Code begleiten die Dokumentation.

Ein vollständiger Neubau wird vermieden. Bestehende Verfahren werden einzeln
angebunden und ihre Schnittstellen überprüft, bevor alte Ablaufwege ersetzt werden.
Der Anwender soll eine kleine Änderung am Beispiel selbst lokalisieren und
ihre Auswirkungen anhand des CI-Berichts beurteilen können.

## Etappe 4 AP 3 und AP 4

AP 3 erzeugt rasterbasierte Startmodelle auch bei leerer oder unbekannter
Beschreibung. AP 4 verbindet Kandidatenpool, Strukturänderungen und
Parameteroptimierung unter einem gemeinsamen Suchbudget. Bei Bedarf wird ein
Budget von beispielsweise 300 Sekunden sinnvoll genutzt; ein erreichtes
Qualitätsziel darf zum früheren Ende führen.

Beschreibungsmuster dürfen die Suche nicht blockieren. Grundformen bleiben
frei kombinierbar, Objektanzahl und Struktur während der Suche veränderbar.
Unzureichende echte Vektorentwürfe bleiben erhalten. Vorhandene mathematische
Algorithmen werden wiederverwendet; bildspezifische Sonderfälle sind keine
primäre Entwicklungsstrategie. AP 5–8 bleiben gemäss AP 0 eingeplant.

## Fortschritt und Rahmen

- [ ] Etappe 1: Betrachtbare Demo und verständliche Architekturübersicht abgenommen.
- [ ] Etappe 2: Ursachenliste und begrenzter Reparaturumfang festgehalten.
- [ ] Etappe 3: Vereinbarte Reparaturpakete geprüft; übrige Fehler dokumentiert.
- [ ] Etappe 4: AP 3 und anschliessend AP 4 umgesetzt und geprüft.

Änderungen bleiben auf `experimental/explorative-conversion` und werden über
[PR 2084](https://github.com/MobyDickDick/ImageConverter/pull/2084) oder einen
passenden nachfolgenden PR bereitgestellt. Tests, Testkonvertierungen und
Benchmarks laufen ausschliesslich auf GitHub Actions. Fehlgeschlagene und
ausstehende Prüfungen werden ausdrücklich genannt. Die unversionierte Datei
`try_exploratory.py` bleibt von diesem Dokumentationsauftrag unberührt.

Grundlagen: [AP 0](AP0_Architekturanalyse_ImageConverter.md),
[AP 1](AP1_Isolierter_Konvertierungskern.md),
[AP 2](AP2_Flexible_geometrische_Repraesentation.md).
