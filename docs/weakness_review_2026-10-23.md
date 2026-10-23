# Schwächenprüfung und neue Arbeitsreihenfolge

Ausgangsstand `9a1f0b661`, neuer Branch
`codex/adaptive-generalization-review-2026-10-23`.
Untersuchungsgrundlage: produktive Szenenerzeugung und Such-Bots, aktuelle
Abnahmeberichte und eine neue echte CLI-Gegenprobe. Zwei beim Start bereits
geänderte Dateien zur realen Transferprüfung gehören nicht zu diesem Paket.

## Befund

Die beiden Vermutungen treffen den zentralen Engpass. Es fehlt weniger an
Parameteroptimierern als an einem Suchraum, der bei einem Fehlschlag eine
andere Zerlegung des Bildes zulässt. Die vorhandene adaptive Suche und ihre
Zeitaufsicht sind sinnvoll; sie ersetzen diese Fähigkeit nicht.

| Gewicht | Schwäche | Nachweis im Ausgangscode und praktische Folge |
| --- | --- | --- |
| Sehr hoch | Struktur wird zu früh festgelegt | `Bot.proposal` in `imageCompositeConverterSearchBots.py` kopiert und verändert einen bestehenden Parametervektor. Es entstehen dadurch keine zusätzlichen Objekte, anderen Formtypen oder Schichten. Mehr Suchzeit allein repariert eine fehlende Struktur nicht. |
| Sehr hoch | Vorhandene Fähigkeiten sind nicht frei kombinierbar | `fit_primitive_scene` springt anhand sprachlicher Merkmale direkt in einzelne Szenenwege. Der gemischte Weg erlaubt nur ein/zwei horizontal getrennte Rechtecke in einem Verlaufskreis; sein einzelner Restbildschwellwert ist 25. Rundung und Überdeckung anderer Module werden hier nicht zusammengesetzt. Der eingefrorene reale Transferversuch scheitert 0/2. |
| Hoch | Beschreibungsvertrag und Erfolg sind nicht überall deckungsgleich | Der reale Transferbericht enthält intern `contract_status=ok` bei unabhängig zurückgewiesenen Ersatzmodellen. Ein Sprachparserstatus ist noch kein Nachweis, dass jedes verlangte Objekt im SVG enthalten ist. Die unabhängigen Gates verhindern dort die positive Abnahme; die produktive Statusgrenze muss dennoch klarer werden. |
| Hoch | Allgemeine Leistungsfähigkeit ist unzureichend gemessen | 379 archivierte Paare sind weder 379 unabhängige Familien noch die aktuelle Erfolgsquote auf 1.785 Quellen. IDO-19/IDO-21 beruhen teilweise auf Vertragsfixtures. Neue reale Übertragung und der praktische Vergleich bleiben offen. |
| Mittel bis hoch | Begrenzter Formen- und Sprachumfang | Geschlossene Szenengrammatiken verhindern das stille Weglassen unbekannter Aussagen, verlangen aber konkrete Formulierungen. Freie Kurven, allgemeine Schichten und beliebige Primitive sind nicht durchgängig angeschlossen. Sprachrobustheit ist nur im geprüften Umfang nachgewiesen. |
| Mittel | Gekoppelte, schwer veränderbare Runtime | Zwei Aufrufe von `_syncRemainingRuntimeBindings` in `imageCompositeConverter.py`, viele frühe Rückgaben und separate Szenenvalidierungen erschweren gemeinsame Suche. Eine reine Dateiaufteilung würde die Kopplung nicht beseitigen. |

Ein negativer Versuch ist erwünscht, wenn er zur nächsten begründeten
Hypothese führt. Ein ungeprüftes SVG als Erfolg auszugeben wäre dagegen kein
Fortschritt. Vorschläge dürfen experimenteller werden; die Abnahme bleibt
objektweise, semantisch und am Originalraster verbindlich.

## Verbindliche Reihenfolge der offenen Pakete

Diese Reihenfolge ersetzt die älteren Hinweise auf das „nächste Paket“ in den
historischen Abschnitten. Bestehende Aufgaben und ihre Restabnahmen bleiben
erhalten; es wird keine frühere Abnahme nachträglich vergrößert.

| Rang | Pakete | Nächster prüfbarer Lieferumfang |
| --- | --- | --- |
| 1 / P0 | **SEARCH-STRUCTURE-01**, danach **GENERAL-SCENE-COMPOSITION-09** | Alternative Restbildzerlegungen unter demselben Bildbudget, erfolglose Vorschläge nachvollziehbar verwerfen, wiederholte Vorschläge vermeiden. Danach gemeinsame Primitive mit Rundung/Überdeckung und Add/Remove/Replace-Operatoren; keine weitere Familienvorlage als Ersatz. |
| 2 / P1 | **SEMANTIC-COMPLETENESS-02**, V5/V6 | Für jeden produktiv erfolgreichen Kandidaten alle Beschreibungsaussagen an native Instanzen und Relationen binden. `unsupported_structure`, Sucherschöpfung und geprüften Erfolg unterscheiden; beschädigte SVGs und unpassende Ersatzmodelle müssen scheitern. |
| 3 / P1 | **GENERAL-SCENE-REAL-05**, IDO-P4/IDO-19/IDO-21, **BENCHMARK-PRACTICAL-01** | Vor weiterer realer Entwicklung neue Familien sperren und unabhängig annotieren; echte CLI-Vergleiche ohne Nachstimmung. Synthetische Entwicklung separat berichten. Praktischen Nutzen einschließlich negativer Fälle, Vergleichsverfahren und menschlicher Zeit messen. |
| 4 / P2 | V2/V3/V4, **PB-LEARN-INVENTORY**, **PB-POOL-2026-10-07** | Nächste fehlende Form-/Verlaufs-/Sichtbarkeitsoperatoren nach gemeinsamen reproduzierten Fehlerursachen auswählen. Quellenprüfung **CATALOG-SOURCE-REVIEW**, GE0305/GE0306/GE0022 vor Verwendung dieser Daten. Graue JPG-/Stressfälle als Robustheitskohorte zusammenfassen, Grenzen beibehalten. |
| 5 / P2 | **COMPONENT-VALUE-02**, **NEURAL-ELEMENTS-01**, V7 | Erst mit aktiven schwierigen Strukturproblemen vergleichen: bestehendes Portfolio, verkleinertes Portfolio und optionale neue Vorschlagsquellen bei gleichen Gesamtbudgets. Kein neues Netz als Ersatz für fehlende Szenenverknüpfung. |
| 6 / P3 | **ARCH-RUNTIME-CONTEXT-01**, **SEARCH-DEADLINE-COMPAT**, Archiv-I/O/-Drift, TB/FP/QR-Restaufgaben | Qualitätsgesicherte Produktionsgrenze entkoppeln, historische Kompatibilität absichern und Test-/Betriebsaltlasten abbauen. Reproduzierte neue Regressionen rücken sofort vor. |

Prüfdaten und Bestandsschutz sind Abhängigkeiten jedes Schrittes, keine erst
bei Rang 3 beginnende Qualitätssicherung. Die größere Produktbereinigung bleibt
entsprechend der Roadmap hinter der Konvertierungsqualität.

## Rang 1 begonnen: SEARCH-STRUCTURE-01

Der erste produktive Teil ist bewusst kleiner als eine allgemeine
Struktursuche. Er untersucht Restbildzerlegungen im bestehenden gemeinsamen
Verlaufskreis-/Rechteckweg, ausschließlich an synthetischen Entwicklungsfällen.
Es wird keine neue reale Familienabnahme beansprucht. Das Sperren zweier
weiterer realer Familien für GENERAL-SCENE-REAL-05/COMPOSITION-09 bleibt offen.

- Bis zu acht Rechteckkinder können aus Restbildkomponenten entstehen,
  unabhängig von einer konkreten Reihen-/Spaltenvorlage. Horizontale und
  vertikale Beschreibungen erzwingen weiterhin ihre jeweilige Anordnung;
  „getrennt voneinander“ erlaubt eine beliebige disjunkte Anordnung.
- Nach einem erfolglosen Restbildvorschlag werden die Schwellwerte 16 und 36
  zusätzlich zum bisherigen Wert 25 untersucht. Diese verändern die
  Vorschlagserzeugung, keine Qualitätsgrenze. Gleiche Geometrie-/Farbvorschläge
  werden innerhalb dieses Aufrufs nicht erneut optimiert.
- Subpixelkanten werden aus der beobachteten Farbmischung mit dem örtlichen
  Verlauf geschätzt. Dadurch hängt die Startgeometrie weniger vom gewählten
  Restbildschwellwert ab.
- Alle Kinder müssen vollständig im Kreis liegen, paarweise getrennt sein
  und ihre lokalen Gates bestehen. Zusätzlich gilt eine volle Rasterprüfung.
  Unbekannte oder widersprüchliche Aussagen bleiben Ablehnungsgründe.
- `scene_attempts` und `[Search]`-Ereignisse zeigen abgelehnte, doppelte und
  angenommene Zerlegungen. Die Aufsicht und das gemeinsame Bildbudget bleiben
  aktiv; ein erschöpftes Budget startet keinen weiteren Versuch.

Die begrenzte Auswahl von drei Zerlegungen ist ein Einstieg in das Experimentieren,
kein freies Erfinden von Konvertierungsalgorithmen. Noch fehlen alternative
Formklassen, zusätzliche/entfernte Instanzen gegen einen gemeinsamen Vertrag,
überlappende Kinder, frei verknüpfte Rundung, dauerhafte negative Evidenz über
mehrere Registrierungen und faire Zeitscheiben für Strukturhypothesen. Ein
schwieriger erster Fit kann weiterhin die Restzeit aufbrauchen.

### Gegenprobe und Grenzen

`tools.evaluate_residual_scene` erzeugt unabhängig vom Detektor native
Referenzgeometrie und Objektmarkierungen. Vor der Runtime-Änderung wurden acht
Fälle über die echte überwachte CLI mit fünf Sekunden je Bild geprüft:
**0/8** bestehen die unabhängigen Objekt-/Regions-/Pixelgates. Diese Fälle und
ihre Eingabeprüfsummen wurden vor der Änderung gesichert.

Die ersten sechs Fälle enthalten vertikale Gruppen sowie drei, vier oder sechs
Rechtecke in unterschiedlichen Anordnungen. Zwei weitere Fälle enthalten sehr
kontrastarme Rechtecke. Sie bleiben ausdrücklich im Nenner, auch wenn der
Detektor nun einen Vorschlag erzeugt. Ein erst während der Entwicklung ergänzter
neunter Fall untersucht zwei durch Antialiasing scheinbar verbundene Rechtecke;
er ist eine zusätzliche Entwicklungskontrolle, kein ursprünglicher Holdout.

Der endgültige echte CLI-Vergleich verbessert die ursprünglichen acht Fälle
von **0/8 auf 6/8**. Die zusätzliche Entwicklungskontrolle besteht **1/1**,
nach zwei verworfenen Zerlegungen beim dritten Schwellwert. Einer der beiden
kontrastarmen Fehlversuche endet am Zeitlimit ohne Ergebniszeile/SVG. Der
gemeinsame Nachprüfer kann diesen Fall nun anhand unabhängiger Aufsichts- und
Zugriffsbelege ausdrücklich als Fehlschlag bestätigen, statt die gesamte
Matrix wegen einer fehlenden Erfolgszeile nicht auszuwerten. Fehlende oder
widersprüchliche Belege bleiben Fehler; sechs gezielte Evidenztests sichern das.

Ergebnisse und Reproduktion stehen unter
[`artifacts/evaluation/residual_scene_v1/README.md`](../artifacts/evaluation/residual_scene_v1/README.md).
Die bestehenden 379 archivierten Paare werden nicht erweitert. Weder dieses
Paket noch neue synthetische Varianten erledigen GENERAL-SCENE-REAL-05.

### Verifikation und offene Testgrenze

- 270 gezielte Szenen-/Regressionsprüfungen bestehen. Nach Wiederherstellung
  des bisherigen Adjektivwortschatzes bestehen 26 Restbildtests; zusammen mit
  den Evidenz-/Transferprüfungen sind es 47 bestandene Tests dieses letzten
  Prüfblocks. Diese Zahlen überschneiden sich und werden nicht addiert.
- Syntaxprüfung, CLI-Hilfe und Runtime-ID-Nullprüfung bestehen. Die gespeicherte
  CLI-Evidenz lässt sich aus ausschließlich den versionierten Dateien erneut
  prüfen: 0/8 vorher, 7/9 endgültig, davon 6/8 identische Vergleichseingaben.
- Archiv-Neukonvertierung: **378/379** im vollständigen Lauf. Bei `AC0910_S`
  fehlen nach einer protokollierten Beobachtungslücke von 3.435,594 Sekunden
  und null Suchauswertungen SVG und Zwischenstand. Die gezielte neue
  Wiederholung besteht **1/1**. Das ist kein nachträglich auf 379/379
  umgeschriebener Erstlauf. Alle 758 gespeicherten Bild-/SVG-Prüfsummen sind
  unverändert; die bestehenden Pixelgrenzen gelten weiter.
- **Keine grüne Gesamtsuite:** Der Standardlauf endet mit 1.688 bestandenen,
  29 übersprungenen und einem fehlgeschlagenen Test. Der unveränderte
  `test_expired_containment_never_releases_worker` misst nach `sleep(1.1)` nur
  1,094 Sekunden und erwartet mindestens 1,100. Die vorgeschalteten funktionalen
  Abbruch-/Nichtfreigabe-Assertions bestehen. Der Fehler ist einzeln reproduziert;
  produktiver Deadline-Code und Test sind bytegleich zum Ausgangscommit.
  Die zwei nachfolgenden Deadline-Tests bestehen. Eine zusätzliche breite
  Fortsetzung wurde ohne vollständiges Ergebnis beendet und zählt nicht als
  Gesamtabnahme. Die Testzeitmessung bleibt beim bestehenden Teststabilitätspaket.

Maschinenlesbare Details und Archivberichte stehen unter `checks.json`,
`archive-recheck.json` und `archive-repeat.json` im Evidenzordner. Der erste
Standardversuch im systemseitigen Tempordner scheiterte zudem an einem
Windows-Zugriffsfehler beim Ersetzen einer `.pyc`-Datei; der oben berichtete
Lauf verwendet einen separaten Tempordner im Workspace.

### Nächster Schritt im selben Paket

**Nachtrag:** Die [fortsetzbaren Strukturzeitscheiben](history/next_arbeitspaket_2026-10-23_structure_scheduler.md)
sind umgesetzt und mit kontrollierter serieller Gegenprobe sowie echter
CLI-Wiederholung (7/9) geprüft. Der folgende Scheduler-Schritt ist damit erledigt;
die anschließenden Struktur-/Kompositions- und realen Abnahmen bleiben offen.

Strukturvorschläge als fortsetzbare Arbeitseinheiten in den vorhandenen Scheduler
bringen. Eine schlechte erste Zerlegung darf nicht das gesamte Optimierungsbudget
verbrauchen. Anschließend die vorhandenen Form-/Rundungs-/Sichtbarkeitsoperatoren
über einen gemeinsamen vollständigen Szenenvertrag zusammensetzen. Vor diesem
realen Entwicklungsschritt andere reale Familien festschreiben; die bereits
offengelegten GE0018/GE0307 sind ausschließlich Entwicklung.
