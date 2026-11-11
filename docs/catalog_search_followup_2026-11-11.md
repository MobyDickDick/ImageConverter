# Zweiter Katalogaudit: Standby, Ergebnisqualität und weiterhin enger Suchraum

Audit des Laufs `catalog-20261111T121521Z-d7a16496`, Seed `1007299007`.
Untersucht wird ein gesicherter Zwischenstand des Laufs vom 11.11.2026,
13:15 bis zum letzten beobachteten Batchereignis um 16:06:53 Uhr
Europe/Zurich. Das ist kein vollständig abgeschlossener Kataloglauf.
Alle folgenden Ergebniszahlen beziehen sich auf diesen unveränderlichen
Snapshot, nicht auf später hinzukommende Ergebnisse.

**Hauptbefund:** Die lange verstrichene Zeit ist größtenteils durch
automatischen Windows-Standby erklärt. Die während tatsächlich abgeschlossener
Bildläufe erreichte Qualität zeigt zugleich weiterhin die im
[ersten Audit](catalog_search_audit_2026-11-11.md) belegten Grenzen:
wenig Strukturvielfalt, keine Modellfreigabe der allgemeinen Nachoptimierungen
und keine dauerhafte Lernschleife im verwendeten Modus.

## 1. Neu belegter Hauptgrund für den geringen Durchsatz: Modern Standby

Die Windows-Systemereignisse des Providers `Microsoft-Windows-Kernel-Power`
belegen folgende Intervalle. Ereignis 506 meldet den Eintritt mit Grund
`Idle Timeout`, Ereignis 507 das Ende mit Grund `Input Keyboard`.

| Eintritt Europe/Zurich | Aufwachen | Intervall |
| --- | --- | ---: |
| 13:20:36,800 | 13:27:24,468 | 6 min 47,7 s |
| 13:33:11,940 | 14:38:54,631 | 65 min 42,7 s |
| 14:44:12,743 | 16:06:53,281 | 82 min 40,5 s |

Zusammen sind dies **155,18 Minuten** innerhalb des rund **171,54 Minuten**
langen beobachteten Batchfensters, also etwa **90,5 Prozent**. Die 32
abgeschlossenen Ergebniszeilen summieren sich dagegen nur auf **990,702
Sekunden**, rund **16,5 Minuten** gemeldete Bildlaufzeit.

Modern Standby ist keine millisekundengenaue Grenze vollständiger
CPU-Inaktivität: Prozesse können in Übergangsphasen noch kurz laufen.
Der Befund stützt sich deshalb zusätzlich auf die unabhängigen Zeitspuren:

| Versuch | Gemeldete Gesamtdauer | Größte Aufsichtslücke | CPU-Zunahme des Aufsichtsprozesses in dieser Lücke |
| --- | ---: | ---: | ---: |
| AC0501_2L_sia | 390,141 s | 387,718 s | 0,000 s |
| AC0820_L | 3.918,359 s | 3.914,969 s | 0,000 s |
| Lueftung | 4.977,703 s | 4.954,219 s | 0,000 s |

Die jeweilige Deadlinebeobachtung liegt weniger als 0,3 Sekunden vom
protokollierten Aufwachereignis entfernt. Die geringe Reihenfolgeabweichung
ist mit asynchroner Ereignisprotokollierung beim Aufwachen vereinbar.
Die Daten belegen keine minuten- oder stundenlang aktiv rechnenden Optimierer.
Die CPU-Angaben betreffen die Aufsicht; sie sind keine vollständige
CPU-Abrechnung aller Worker.

Das Bildbudget beträgt regulär 60 Sekunden, mit äußerer Obergrenze von 120
Sekunden bei zulässigem Fortschritt. Der laufende Rechner ist Voraussetzung
der Aufsicht. Nach dem Aufwachen zählt die verstrichene Standbyzeit gegen
das Budget; der Worker wird als Timeout verworfen. Alle drei Fälle besitzen
keinen geretteten geprüften Zwischenstand. Aus deren gemeldetem
`candidate_evaluations=0` lässt sich nicht ableiten, dass intern überhaupt
keine Vorschläge versucht wurden: Der abgebrochene Worker konnte keinen
vollständigen Ergebnisbericht mehr übergeben.

Dies ist ein erneutes Auftreten der bereits
[am 22.10. untersuchten Betriebsgrenze](history/next_arbeitspaket_2026-10-22_deadline_overrun_audit.md).
Die damalige Arbeit hat Phasenmessung und Deadlinebelege verbessert;
sie hat automatischen Standby während einer Konvertierung nicht verhindert.
Im aktuellen Repository wurde keine explizite Betriebssystemanforderung
gefunden, die den Rechner während aktiver Katalogberechnung wach hält.

## 2. Ergebnisstand und unabhängige Nachprüfung

| Beobachtung im Snapshot | Ergebnis |
| --- | ---: |
| Ausgewählte Eingaben | 1.787 |
| Begonnene Eingaben | 36 |
| Gespeicherte Ergebnisse | 32 |
| Fehler im Batch-Ereignisprotokoll | 3 |
| Begonnen ohne Abschluss im Snapshot | 1: DLG0018 |
| Vom Konverter modellbestätigt | **3/32** |
| Unabhängig erneut bestandene reine Pixelgates | **11/32** |
| Pixelpass ohne vollständige Modellbestätigung | **8/32** |
| Median abgeschlossener Bildlaufzeit | 32,672 s |
| Gemeldete Renderauswertungen | 54.702 |
| Bot-Parametervorschläge | 73.551 |
| Davon gültig / verworfen | 42.551 / 31.000 |

Die drei Modellfreigaben sind `AC0414_1_M`, `AC0920_M` und `GE9034_6S`.
Die elf Pixelpässe sind keine vollständige unabhängige Objekt-/Semantikabnahme.
Es wäre falsch, die übrigen acht allein wegen ihres Rasterwerts automatisch
freizugeben. Einige sind bei der visuellen Gegenprüfung allerdings bereits
brauchbar: etwa das Klappensymbol `AC0501_S` und die Verlaufsfläche `NAV0010`.
Hier fehlt vor allem eine passende fachliche Modellbestätigung des allgemeinen
Ausgabepfads.

Auf der anderen Seite bleiben große sichtbare Strukturfehler:

| Eingabe | Original | Gespeicherter Entwurf |
| --- | --- | --- |
| AC0030_S | Zwei verschiedenfarbige senkrechte Pfeile | Rechteckige Linienstruktur ohne Pfeilspitzen |
| AC0303_1_M | Roter Kreis mit hellen Innenlinien | Rotes Verlaufsrechteck ohne Innenlinien |
| AC0504_1M_sia | Zusammengesetztes Symbol mit Anschluss, Kreis und Diagonale | Zwei rosa rechtwinklige Randlinien |
| GE0362 | Schraubenschlüssel, Schraubendreher und Flamme | Im Wesentlichen die Hintergrundscheibe und kleine unpassende Zeichen |

`AC0303_1_M` zeigt zusätzlich eine unzureichende Beschreibung: ein
Referenztext spricht allgemein von einem Kompressor und grauem Hintergrund,
während das konkrete Raster einen roten Kreis zeigt. `AC0504_1M_sia` wird
ausdrücklich nur als unklassifiziertes Bildobjekt beschrieben. `GE0362`
enthält fachliche Referenzen auf mehrere Symbole, die derzeit nicht zu einer
vollständigen geometrischen Konstruktion zusammengesetzt werden.

Ein lokales Vergleichsblatt liegt unter
`.tmp/catalog-search-audit-20261111-long/comparison.png`. Für diesen Audit
wurden keine Bilder neu konvertiert; die vorhandenen SVGs wurden für die
Messung erneut gerendert.

## 3. Die wesentlichen Suchgrenzen sind unverändert

**28 von 32 Bildern** verwenden weiterhin `native_svg_continuation`.
Alle 28 optimieren ihren anfänglich festgelegten SVG-Aufbau; **0/28** erhalten
eine Modellfreigabe. Im Protokoll gibt es 515 Bot-Neustarts, aber keine
`scene_hypothesis`- oder `structure_search_finished`-Ereignisse der gemeinsamen
Struktursuche. Die vorhandenen Beschreibungen erfüllen auch im aktuell
geprüften Code **0/32** der engen Mischszenenverträge.

Die übrigen vier Registrierungen kommen aus zwei bekannten
Verlaufs-/Linienmodellen, einem Kreis-Linienmodell und einem beschrifteten
Kreismodell. Die große Zahl von Parameterversuchen bedeutet deshalb
weiterhin keine breite Erkundung verschiedener vollständiger Konstruktionen.
Eine falsch vorgewählte Rechteckform wird durch weitere Farb-, Positions-
und Strichbreitenänderungen nicht zu einem Kreis mit Innenlinien.

Der Modus ist erneut `semantic-only`; eine dauerhafte Strategielernschleife
ist hier nicht angeschlossen. Der neuronale Detektor ist bei allen 32
abgeschlossenen Bildern deaktiviert. Der Batch steht weiterhin auf
`initial_pass`: Die zusätzlichen Katalog-Qualitätsrunden werden erst nach
dem vollständigen Erstdurchlauf aller ausgewählten Eingaben erreicht.

Die 31.000 verworfenen Vorschläge entsprechen rund 42 Prozent der
Botvorschläge. Das ist kein entsprechender Zeitanteil, weil eine frühe
Parameterablehnung viel billiger als Rendering sein kann. Vorrangig bleibt
die fehlende Strukturvielfalt, nicht die bloße Zahl ungültiger Vorschläge.

## 4. Zwei Reportingprobleme bestehen fort; eines ist zusätzlich konkret belegt

**Veralteter Fehlerwert:** Bei allen 28 nachoptimierten Ausgaben stimmt
`best_error` weiterhin nicht mit dem mittleren absoluten Fehler des
gespeicherten SVGs überein. `mean_delta2` wurde dagegen am aktuellen SVG
nachgemessen. Die Ursache ist die bereits im ersten Audit belegte
SVG-Ersetzung im Artefaktcallback ohne entsprechende Aktualisierung des
ursprünglichen Fit-Rückgabefehlers. Die neue Laufzeit hat diesen Codefehler
nicht verändert.

**Verzögerter Fehler-Checkpoint:** Der Snapshot enthält drei
`variant_failed`-Ereignisse, aber nur zwei Fehler in Checkpoint und
`batch_failure_summary.csv`. Der dritte Fehler, `Lueftung`, fehlt dort.
Der Checkpoint zeigt noch das zuletzt gespeicherte Ergebnis `AC0301_L_SIA`
mit Index 34, während bereits Index 36, `DLG0018`, begonnen wurde.

Die Ursache ist im
[Erstdurchlauf](../src/iCCModules/imageCompositeConverterConversionInitialPass.py)
sichtbar: Der Fehlerzweig protokolliert `variant_failed` und führt `continue`
aus, bevor der weiter unten stehende inkrementelle Checkpoint aufgerufen
wird. Nach einem Fehler bleiben die Übersichten deshalb bis zum nächsten
Checkpoint zurück. Für zuverlässige Fortschrittsanzeigen und Wiederaufnahme
sind Zustände bei Start, Fehler, Abschluss und Unterbrechung unmittelbar
und konsistent zu persistieren.

## 5. Vergleich mit dem ersten Audit

Der erste Audit hatte 38 gespeicherte Ausgaben, zehn Modellfreigaben und 13
reine Pixelpässe. Dieser Snapshot enthält 32, drei bzw. elf. Die Pixelpassanteile
liegen damit ähnlich bei rund 34 Prozent. Das ist wegen der unterschiedlichen
Zufallsauswahl keine kontrollierte Messung einer Qualitätsveränderung.

Nur **AC0251_2** kommt in beiden Stichproben identisch vor. Beide Ausgaben
bleiben Pixelpässe ohne Modellfreigabe. Der normalisierte MSE sinkt geringfügig
von 0,00158842 auf 0,00158617; die Kantenmetrik steigt von 0,9393 auf 0,9464.
Daraus ist weder eine allgemeine Verbesserung noch eine allgemeine
Verschlechterung der Software abzuleiten. Eine automatische Lernwirkung
zwischen diesen Läufen ist nicht belegt.

## Priorisierte Konsequenzen

1. **Vor weiteren langen Katalogläufen automatische Unterbrechungen behandeln:**
   Während aktiver Berechnung eine zeitlich begrenzte Wachhalteanforderung
   der Anwendung verwenden; der Bildschirm kann weiterhin abschalten.
   Tatsächliche Unterbrechungen gesondert protokollieren und anschließend
   kontrolliert fortsetzen bzw. neu einplanen. Standbyminuten nicht als
   geleistete Optimierungsarbeit darstellen.
2. **Ergebnisse und Fortschritt zuverlässig sichern:** unveränderliche
   Laufordner, Checkpoints auch bei Fehlern und aktivem Bild sowie separate
   Kennzeichnung von geprüftem Ergebnis und ungeprüftem Entwurf. Aktuelle
   SVG-Metriken zusammen mit dem betreffenden SVG übernehmen.
3. **Für bessere Bildqualität den tatsächlich benutzten Fallback erweitern:**
   alternative vollständige Konstruktionen, wechselbare Formtypen und
   ergänzbare Linien-/Symbolgruppen aus unerklärten Bildregionen erproben.
   Kleine Bildgruppen mit unmittelbarer Rückmeldung verwenden, statt
   Verbesserungsrunden bis zum gesamten Katalogende aufzuschieben.
4. **Gut passende allgemeine Ausgaben fachlich prüfen können:** Für die acht
   Pixelpass-Entwürfe fehlt eine belastbare semantische/objektbezogene
   Bestätigung. Diese Prüfung ergänzen, ohne die vorhandenen Grenzen
   pauschal zu lockern oder Entwürfe in Erfolge umzubenennen.

Mehr Wachzeit verbessert den Durchsatz, schafft aber allein noch keine
fehlenden Formen. Die Strukturerweiterung bleibt daher die fachliche
Hauptarbeit für die gewünschte breitere Konvertierungsqualität.

## Nachweise und Grenzen

[Maschinenlesbare Auswertung](../artifacts/evaluation/catalog_search_followup_v1/summary.json):
Snapshot-/Einzeldateihashes, Ergebnisse aller 32 Ausgaben, unabhängige
Rastermetriken, Windows-Ereigniskennungen, UTC-Zeitpaare, Aufsichtslücken,
CPU-Differenzen, Fehlerübersichten und der eine gepaarte Vergleich.

Die Rohdaten wurden vor der Analyse unter
`.tmp/catalog-search-audit-20261111-long/` separat gesichert. Timingdateien
können mehrere historische Versuche enthalten; die drei Standbykorrelationen
verwenden jeweils die zum aktuellen Lauf gehörende Versuch-ID. Die 32
ausgewerteten Workerlogs und Komponentenprotokolle enthalten jeweils genau
eine Ausführung bzw. Konfiguration. Globale historische Suchlogs werden
nicht als zusätzliche Arbeit dieses Laufes gezählt.

Es wurden keine Produktionseinstellungen, keine Energieoptionen und keine
Konvertierungsergebnisse verändert. Der Audit bewertet vorhandene Daten;
er ist keine neue reale Gesamtabnahme oder abgeschlossene Fehlerbehebung.
