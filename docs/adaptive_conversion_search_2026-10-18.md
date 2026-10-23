# Adaptive Konvertierungssuche (2026-10-18)

**Suchscheduler:** Fortsetzbare Modellregistrierungen, gemeinsame Zeitscheiben,
Fortschritt pro aktiver Sekunde und reservierte Erkundung sind jetzt als
[SEARCH-SCHEDULER-02](history/next_arbeitspaket_2026-10-18_search_scheduler.md)
angeschlossen. Die folgenden Zahlen beschreiben den damaligen Ausgangsstand.

**Folgepaket:** Die reguläre `semantic-only`-CLI umfasst jetzt die kooperative
Suche mit einer [durchgängigen Prozessaufsicht](history/next_arbeitspaket_2026-10-18_search_deadline.md)
einschließlich Abschlussprüfung und gesicherter Zwischenstandübergabe. Die weiter
unten beschriebene rein kooperative Grenze gilt für den ausdrücklich gewählten
direkten Ablauf und historische Kompatibilitätspfade.

Die Suche richtet ihren Aufwand jetzt nach Ergebnis und gemessenem Fortschritt.
Der Standardaufruf verwendet `--search-mode portfolio --search-policy adaptive`.
Der Branch `codex/adaptive-conversion-search-2026-10-18` baut auf `09ec51af9` auf.
Die feste Suche bleibt mit `--search-policy fixed` reproduzierbar aufrufbar.

**Erweiterung:** Die zusätzliche adaptive Suche verwendet jetzt
[sechs kooperierende Bots](bot_conversion_search_2026-10-18.md) mit eigenem
Suchzustand, Nachrichtenaustausch, Abschaltung und Bild-/Modellgedächtnis.
Die unten beschriebenen drei Suchwege und ihre historischen Messungen beziehen
sich auf die erste adaptive Version. Zeit-, Fortschritts- und Qualitätsgrenzen
gelten weiter; die Bots teilen sich das vorhandene Vorschlagsbudget.

## Entscheidungsregeln

| Beobachtung | Verhalten |
|---|---|
| Ein Kandidat erfüllt die bisherigen strengen Pixelgrenzen und die lokalen Objekt-/Textprüfungen | Die angeschlossene Registrierung beendet die Optimierung. Nach tatsächlicher Auswahl dieses SVGs entfallen weitere Qualitätswiederholungen. |
| Noch kein zufriedenstellender Kandidat, aber messbarer Fortschritt | Weiterarbeiten und die vorhandenen alternativen Suchwege in kurzen Abschnitten vergleichen. |
| Deutliche Verbesserung kurz vor Ende des normalen Zeitbudgets | Zeit in zusätzlichen Abschnitten von 15 Sekunden bereitstellen, bis zum konfigurierten Höchstbudget. |
| Verbesserung kurz vor Ausschöpfen der zusätzlichen Vorschläge | Vorschlagsbudget schrittweise erhöhen, höchstens auf das Vierfache der Basis. |
| Alle drei zusätzlichen Suchwege wurden versucht, seit 128 Vorschlägen kein deutlicher Fortschritt | Zusätzliche Parametersuche mit Grund `stagnation` beenden; andere noch verfügbare Modellhypothesen bleiben möglich. |
| Ein kompletter erneuter Bildlauf bringt keine relevante Qualitätsverbesserung | Bisheriges besseres SVG erhalten und weitere Wiederholungen dieses Bildes beenden. |
| Zeitlimit, äußerste Vorschlagsgrenze oder zulässiger Suchraum erschöpft | Besten zulässigen Zwischenstand zurückgeben; ein unzureichendes Ergebnis wird dadurch nicht erfolgreich. |

Ein schlechter Start allein löst keinen Stagnationsabbruch aus. Auch die ältere,
historisch begründete Qualitätsvorprobe darf im adaptiven Modus einen schlechten
Start nicht als aussichtslos abweisen. Ihre bisherige Faktorgrenze wird dort
deaktiviert; im festen Modus bleibt sie erhalten.

„Deutlicher Fortschritt“ bedeutet eine kumulierte Verbesserung von mindestens
einem Prozent gegenüber dem letzten maßgeblichen Vergleichswert. Kleine
Einzelschritte können sich dazu summieren. Fehlgeschlagene Renderaufrufe,
unzulässige Kandidaten, Verschlechterungen und Messrauschen kaufen keine
Verlängerung. Zusätzliche Vorschläge berücksichtigen das bisherige
Optimierungsmaß; die geteilte Zeitsteuerung verwendet nur tatsächlich
übernommene, zulässige Fehlerverbesserungen. Eine Verbesserung kann nicht
mehrfach dieselbe Verlängerung auslösen.

Eine Zeitverlängerung verlangt Fortschritt im letzten Zeitfenster vor der
aktuellen Grenze: höchstens zehn Sekunden, bei kürzeren Budgets entsprechend
kleiner. Ohne solchen Fortschritt endet die angeschlossene Suche an der
normalen Zeitgrenze. Fortlaufender Fortschritt darf die äußerste Grenze niemals
verschieben.

## Gemeinsame Zeit und sichere frühe Erfolge

Ein `ImageSearch`-Kontext begleitet jedes Bild über seine Modellhypothesen und
Qualitätswiederholungen hinweg. Das normale Budget beträgt 60 Sekunden, das
äußerste Budget 120 Sekunden. Zwischen zwei Bearbeitungsabschnitten desselben
Bildes pausiert die Uhr: Andere Bilder eines Batches verbrauchen dessen Budget
nicht. Ein weiterer Modellversuch oder erneuter Qualitätslauf startet die Uhr
nicht neu. Jede neue Bilddatei erhält einen eigenen Kontext.

Ein Pixelpass allein reicht nicht zur Erfolgsfreigabe. Kreisscheiben mit
einzelnen Buchstaben, Kurztexte, das zusammengesetzte Ventil und unterstützte
Primitive besitzen callbacks für ihre bestehenden semantischen Prüfungen.
Der Optimierer darf bei diesen Modellen bereits am Startkandidaten oder nach
einem Verbesserungsabschnitt aufhören. Andere angeschlossene Formregistrierer
behalten ihre abschließende lokale Prüfung und können danach einen
zufriedenstellenden Kandidaten melden.

Die Freigabe wird an Hashes der tatsächlichen Quellpixel und des geprüften SVGs
gebunden. Die Batchlogik überspringt weitere Qualitätsversuche nur dann, wenn
genau dieses SVG tatsächlich als Ausgabe erhalten bleibt. Ein abgewiesener
Zwischenkandidat, eine andere gewählte Ausgabe oder geänderte Quellpixel dürfen
keine alte Freigabe übernehmen. Ein abgewiesener Qualitätsversuch überschreibt
weiterhin keine bessere Ausgabe.

Die Pixelgrenzen bleiben unverändert: normalisierter MSE höchstens 0,01,
Vordergrund-MSE höchstens 0,04, Vordergrund-IoU mindestens 0,85 und
Kantenausrichtung mindestens 0,72. Hintergrund und Masken werden wie in der
unabhängigen Plan-B-Abnahme aus dem tatsächlichen Bildrand ermittelt. Die
ältere Annahme eines immer rein weißen Bildrandes konnte einen beschnittenen
Lux-Fall zu früh freigeben; die neue Gegenprobe verhindert dies.

Die neue Priorität ist ein früh erreichtes **ausreichendes** Ergebnis. Weitere
Rechenzeit könnte seine Messwerte noch verbessern. Die adaptive Ausgabe muss
deshalb nicht pixelgleich zum vollständig ausoptimierten festen Fit sein.
Gespeicherte Bestresultate und Qualitätsgrenzen bleiben erhalten.

## Einstellungen und bestehende Grenzen

```powershell
.venv/Scripts/python.exe -m src.imageCompositeConverter EINGABE --descriptions-path BESCHREIBUNGEN.xml --output-dir AUSGABE --start ERSTES --end LETZTES --search-policy adaptive --search-seconds 60 --search-max-seconds 120 --search-budget 384 --search-seed 42
```

`--search-budget` bezeichnet im adaptiven Modus die Basis **zusätzlicher**
Vorschläge pro Modell. Ursprüngliche Koordinatenregistrierung und Prüfungen
kommen hinzu. Bei spätem Fortschritt können bis zu vier Basisbudgets genutzt
werden; ohne Fortschritt endet die Suche früher. Die drei vorhandenen
Suchverfahren erhalten abwechselnd kleine Abschnitte. Neue gekoppelte
Vorschläge sind über einen einzigen festen Durchlauf hinaus möglich;
identische Parameter werden nicht mehrfach geprüft.

`search/progress.jsonl` zeigt unter anderem `time_extended`,
`proposal_budget_extended`, `search_finished`, `candidate_satisfactory` und
`image_search_finished`. Die Ergebniszeilen enthalten `search_control` mit
verbrauchter aktiver Zeit, Grenzen, Verlängerungen und Abbruchgrund.
`candidate_evaluations` zählt die vermessenen Optimierungskandidaten;
Schrift-Initialisierung und zusätzliche semantische Prüf-Renderings sind darin
nicht als Parameterkandidaten enthalten. Die Registrierung berichtet ihre
Renderaufrufe gesondert.

**Die Zeitsteuerung ist kooperativ.** Sie ist an `_register`, die zusätzliche
Portfoliosuche und die Batchwiederholungen angeschlossen. Sie kann einen
blockierten nativen Renderer nicht während seines Aufrufs unterbrechen.
Unverbundene ältere Optimierer erhalten damit noch keine neue harte
Unterbrechung. Der bestehende Renderer-Timeout und ein externer Prozesswächter
bleiben im direkten Ablauf für diese Fälle erforderlich. Im regulären
`semantic-only`-CLI-Pfad übernimmt inzwischen SEARCH-DEADLINE-01 diese
[Prozessaufsicht samt Zwischenstandübergabe](history/next_arbeitspaket_2026-10-18_search_deadline.md).

Der Katalogrunner kann die adaptive Suche mit einer harten Prozessgrenze
absichern:

```powershell
.venv/Scripts/python.exe -m tools.run_catalog_conversion --timeout-seconds 60 --adaptive-max-seconds 120 --output-dir .tmp/adaptive-catalog
```

Dabei gelten 60 Sekunden als normales Suchbudget und 120 Sekunden als äußerste
Konvertierungsgrenze; der Prozess erhält wie bisher 15 Sekunden zusätzliche
Start-/Abschlussreserve. Ohne `--adaptive-max-seconds` behält der Runner seine
bisherige feste Grenze. Eine ausdrücklich engere externe Grenze hat Vorrang.

Ein Seed reproduziert die Vorschlagsfolge bei gleichem Ablauf. Zeitabhängige
Abbrüche können je nach Rechner und Last an anderer Stelle eintreten.
`--search-policy fixed` ist für den Vergleich mit dem bisherigen festen Ablauf
vorgesehen. `--search-mode legacy` schaltet das zusätzliche Portfolio weiterhin
ab. `semantic-only` liest nach wie vor keine gespeicherten Referenz-SVGs oder
Strategiestatistik.

Die adaptive Steuerung erzeugt keine bislang unbekannten Topologien oder
Konvertierungsalgorithmen. Die allgemeine Szenensuche und ein gemeinsamer
Vergleich aller Formfamilien bleiben separate Aufgaben.

## Tatsächliche Nachweise

Unter `artifacts/evaluation/adaptive_search_v1/` werden die tatsächlichen
CLI-Ausgaben und ihre erneute unabhängige Messung erhalten. Acht positive Fälle
verwenden neutrale Namen und geschützte Eingabekopien: drei Ventilgrößen, eine
Q-Scheibe mit Griff, rF, Lux sowie zwei unabhängige Szenen aus Grundformen.
Alle acht adaptiven Ausgaben bestehen die unveränderten strengen Pixelgates
und die unabhängige jeweilige Objekt-/Textprüfung. Der Zugriffswächter meldet
keine verbotenen Referenz-SVG-Lesezugriffe.

| Fall | Renderaufrufe des ausgewählten festen Fits | Renderaufrufe des ausgewählten adaptiven Fits |
|---|---:|---:|
| Ventil L | 533 | 225 |
| Ventil M | 532 | 9 |
| Ventil S | 540 | 9 |
| Q mit Griff M | 249 | 26 |
| rF M | 211 | 106 |
| Lux S | 492 | 399 |
| Unabhängige Grundformszene 1 | 226 | 83 |
| Unabhängige Grundformszene 2 | 330 | 40 |

Die Tabelle zählt den ausgewählten Fit, nicht alle zuvor verworfenen
Textmodelle oder frühere Qualitätsläufe. Diese stehen separat in den Logs und
Ergebniszeilen. Der feste Modus reproduziert die drei vorher akzeptierten
Ventil-SVGs bytegleich. Der bekannte seedabhängige Lux-S-Fall bleibt als
Kontrolle sichtbar; die neue adaptive Ausgabe besteht ihr strenges Pixelgate.

Die unabhängige grüne R-Ventilvorlage besteht mit Original und 16 Zufallsfällen
**17/17 echte CLI-Konvertierungen**. Die Laufzeiten einschließlich Prozessstart
lagen hier zwischen etwa 1,2 und 3,4 Sekunden unter paralleler Testlast.
Dies ist ein konkreter Nachweis, keine allgemeine Laufzeitgarantie.

Die Zeitverlängerung wird zusätzlich mit einer injizierten monotonen Uhr
geprüft. Diese Tests sind ausdrücklich Steuerungstests mit simulierter Zeit,
keine behaupteten minutenlangen CLI-Erfolge. Sie decken späte und fortgesetzte
Verbesserungen, Rauschen, Plateau, endgültige Zeit- und Vorschlagsgrenzen,
Bildwechsel, verschachtelte Kontexte und wiederaufgenommene Bilder ab.
Weitere Tests prüfen falsche Frühfreigaben und den Schutz der besseren Ausgabe.

Vollständige Test- und Archivberichte sowie Befehle werden im Nachweisordner
gesichert. Die 377 bestehenden Archivpaare werden bei der Prüfung nur aus
Kopien neu konvertiert; ihre Originale, gespeicherten SVGs und Datensätze bleiben
unverändert.
