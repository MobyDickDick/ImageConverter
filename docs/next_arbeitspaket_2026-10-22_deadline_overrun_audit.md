# SEARCH-DEADLINE-OVERRUN-AUDIT – Standby und getrennte Prozesszeiten

Ausgangsstand: `49c5de54f`, Branch
`codex/search-deadline-overrun-audit-2026-10-22`.
Die Ursachenuntersuchung ist abgeschlossen. Der ursprüngliche Überlauf fällt
mit modernem Windows-Standby zusammen. Die Zeitaufsicht benötigt einen laufenden
Hauptprozess; sie garantiert keine Echtzeitgrenze während Standby, fehlender
Prozessorzuteilung oder blockierender Systemoperationen.

## Ursprünglicher Fehlversuch

Der gespeicherte Fall `item04p2` aus `accepted-after-dev` weist weiterhin
261,734 Sekunden Bildzeit, null Suchauswertungen und keine freigegebene Ausgabe
aus. Der äußere Versuch dauerte 263,313 Sekunden und endete mit Rückgabecode 0;
der unabhängige Prüfer erkennt die fehlende Ausgabe trotzdem als Fehler.
Zehn Sekunden Bildbudget und 40 Sekunden nominelles äußeres Timeout wurden
überschritten. Code 0 ist hier kein fachlicher Erfolg.

Die getrennt exportierten Systemereignisse zeigen am 22.10.2026:

| Ereignis | UTC | Europe/Zurich |
| --- | --- | --- |
| Moderner Standby, Grund `Lid`, Ereignis 506 | 07:06:52,386 | 09:06:52,386 |
| Ende des Standby, Grund `Lid`, Ereignis 507 | 07:11:13,964 | 09:11:13,964 |

Das sind rund 261,578 Sekunden. Der Deadlinebericht wurde um
07:11:13,786 UTC geschrieben; sein rückgerechneter Beginn liegt ungefähr bei
07:06:52,052 UTC. Diese Rückrechnung verwendet die Dateizeit und ist keine
damals gespeicherte Startmarke. Die geringe Reihenfolgeabweichung beim Aufwachen
zeigt zudem, dass Ereignisprotokoll und Dateischreibzeit keine exakte gemeinsame
Phasengrenze liefern. Die enge zeitliche Übereinstimmung belegt Standby als
Betriebsursache des langen Wandzeitintervalls. Ob der alte Worker davor schon
gestartet oder bereit war, lässt sich ohne damalige Phasenspur nicht bestimmen.
Ein 261 Sekunden rechnender Suchoptimierer ist durch diese Daten nicht belegt.

Der vollständige historische 80-Versuche-Lauf wurde unabhängig erneut geprüft:
49/50 positive Fälle und 30/30 sichere Zurückweisungen. Seine bereits vorhandene,
bei unverändertem damaligem Code und Protokoll durchgeführte vollständige
Wiederholung `replayed-after-dev` besteht getrennt mit 50/50 und 30/30.
Der Fehlversuch bleibt im Nenner: zusammen 159/160 Versuche, davon 99/100 positiv
und 60/60 negative Fälle. Die übrigen Sprachrobustheitsläufe und deren
Gesamtnenner bleiben wie im ursprünglichen Paket dokumentiert.

## Neue Phasenbelege und Korrekturen

Die reguläre Aufsicht schreibt pro Bild und Versuch eine dauerhafte
`reports/<name>_timing.jsonl`. Versuch-ID und Prozess-ID trennen Wiederholungen.
Jede Marke enthält monotone Zeit, Unix-/UTC-Zeit, Prozess-CPU-Zeit und die
Beobachtungslücke zur vorherigen Marke. Prozessstart, Workerbereitschaft,
Eindämmung/Freigabe, Runtime-Import, Konvertierungsbeginn/-ende, Übergabe und
Abbau sind getrennt. Die Aufsicht protokolliert während des Wartens etwa einmal
pro Sekunde. Workerzeitmarken werden zusammen mit ihrer Empfangszeit erhalten.
Einzelne Lücken belegen allein weder Standby noch einen bestimmten Blockierer.

Bei der Untersuchung entstand ein weiterer unbeabsichtigter Überlauf eines
blockierenden Testworkers: 968,375 Sekunden Gesamtdauer bei 1,5 Sekunden Budget.
Seine vollständige neue Phasenspur zeigt:

- Bereitschaft 0,391 Sekunden nach Rückkehr aus dem Prozessstart.
- Eine 967,000-Sekunden-Lücke zwischen Aufsichtspoll und Deadlinebeobachtung,
  bei 967,004 Sekunden UTC-Differenz und 0,015625 Sekunden zusätzlicher CPU-Zeit
  des beobachtenden Prozesses.
- Prozessabbau danach 0,187 Sekunden; der Worker ist anschließend beendet.
- Keine neue finale Ausgabe. Der bestehende Test scheitert korrekt an seiner
  Zeitbehauptung; der Fehlversuch bleibt als Beleg erhalten.

Auch dieses Zeitfenster enthält Windows-Standbyereignisse: erneuter Eintritt
um 12:45:31 UTC und Aufwachen um 13:01:43 UTC. Der neue Teststart liegt kurz
nach dem protokollierten Eintritt. Moderner Standby ist damit kein exakter
Nachweis des Ausführungszustands jedes Prozesses in jedem Zwischenmoment;
Energieereignisse, Aufsichtslücke und geringe CPU-Zunahme stützen gemeinsam
eine systembedingte Unterbrechung statt langsamen Prozessabbaus.

Zwei begrenzte Korrekturen ergänzen die Diagnose:

- Das äußere CLI-Prüfwerkzeug zählt den Prozessstart nun gegen sein Gesamtbudget.
  Kleine Warteabschnitte protokollieren die Aufsicht. Ein erst nach dem Ablauf
  beobachteter Rückgabecode 0 zählt als Timeout. Start, Kill-Aufruf und Warten
  auf Prozessende erhalten eigene Marken. Das bisherige Werkzeug maß dagegen
  erst nach Prozessanlage mit `subprocess.run(timeout=...)` und prüfte nach
  erfolgreicher Rückkehr die gesamte verstrichene Zeit nicht erneut.
- Die Bildaufsicht gibt einen bereiten Worker nach dem Installieren der
  Eindämmung nur frei, wenn das Bildbudget noch läuft. Eine langsame
  Eindämmungsoperation startet dadurch keine neue Konvertierung nach Ablauf.

Synchroner Prozessstart, Dateizugriffe, Logschreiben und Betriebssystemaufrufe
können selbst blockieren; ihre neuen Zeitmarken lokalisieren die Lücke nach
Wiederaufnahme. Sie machen diese Operationen nicht präemptiv unterbrechbar.
Auch das äußere Prüfwerkzeug ist kein vom Rechner unabhängiger Watchdog.
Es beendet beim äußeren Timeout den CLI-Prozess; seine Phasenspur beweist
allein keine zusätzliche allgemeine Prozessbaumgarantie. Die reguläre
Bildaufsicht verwendet weiter ihr vorhandenes Jobobjekt bzw. ihre Prozessgruppe.

## Abnahme und Grenzen

77/77 gezielte Tests bestehen ohne Überspringen oder erwartete Fehler.
Sie umfassen echte Prozessbäume, Zwischenstandsrettung, verspätete Übergaben,
kontrolliert verzögerten Prozessstart, eine pausierte Aufsicht, abgelaufene
Eindämmung und manipulierte Zeitbelege. Der erste Testlauf im Sandbox-Tempbereich
enthielt 10 Fehler bei 58 bestandenen Tests, hauptsächlich verweigerte atomare
Dateiumbenennungen. Der folgende Debuglauf im Workspace enthielt den oben
dokumentierten Standbyüberlauf (ein bestandener, ein fehlgeschlagener Test).
Danach bestehen 68/68 und abschließend der erweiterte 77/77-Testumfang im
Workspace. Diese Wiederholungen löschen keine früheren Fehlschläge.

Drei neue echte CLI-Zielwiederholungen mit unverändertem Raster/Text, Seed 17,
64 Iterationen und zehn Sekunden Bildbudget bestehen unabhängig erneut.
Die gesamten Werkzeugzeiten betragen 5,140, 4,937 und 4,891 Sekunden.
Diese gezielten Wiederholungen sind keine neue vollständige 80-Fälle-Messung.

Acht zusätzliche direkte/überwachte Produktionsgegenproben erzeugen bytegleiche
SVGs und bestehen die bestehenden strengen Pixel-/Semantikprüfungen. Ein echter
geprüfter Ventilfit bleibt nach absichtlich blockierter Abschlussprüfung erhalten.
Alle gespeicherten 377 Archivpaare und ihr Index sind gegenüber dem früheren
Snapshot hashgleich; eine erneute vollständige Archiv-Neukonvertierung war
für diese reine Zeitaufsichtsänderung nicht Teil der Abnahme.
Budgets, Modellwahl, Semantik- und Qualitätsgrenzen bleiben unverändert.
Keine neue Familien-, Katalog- oder Geschwindigkeitsabnahme wird behauptet.

## Reproduktion

Alle neuen Ausgabeverzeichnisse müssen frei sein. Der Auditprüfer verwendet
die vollständigen lokalen Belege des Sprachrobustheitspakets. Ein frischer
Checkout muss diese nach dessen Dokumentation neu erzeugen; historische
Windows-Systemereignisse sind nur verfügbar, solange das lokale Log sie behält.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_conversion_timing.py tests/test_conversion_deadline.py tests/detailtests/test_plan_b_variations.py tests/test_semantic_robustness_evaluation.py -q --basetemp=.tmp/deadline-tests-new --junitxml=.tmp/deadline-tests-new.xml
.venv/Scripts/python.exe -m tools.audit_deadline_overrun --prepared .tmp/semantic01/frozen-dev --historical-run .tmp/semantic01/accepted-after-dev --output .tmp/deadline-replay-new
.venv/Scripts/python.exe -m tools.audit_deadline_overrun --verify .tmp/deadline-replay-new
.venv/Scripts/python.exe -m tools.evaluate_semantic_robustness --verify .tmp/semantic01/replayed-after-dev --prepared .tmp/semantic01/frozen-dev --require-all
.venv/Scripts/python.exe -m tools.run_deadline_evidence --output-dir .tmp/deadline-quality-new
.venv/Scripts/python.exe -m tools.audit_deadline_overrun --trace artifacts/evaluation/deadline_overrun_audit_v1/observer-gap.jsonl
./tools/export_deadline_power_events.ps1 -StartUtc '2026-10-22T07:05:00Z' -EndUtc '2026-10-22T07:12:30Z' -OutputPath .tmp/historical-power-events-new.json
```

Der Ereignisexport liest ausschließlich die beiden Energieprovider im gewählten
Zeitfenster. Dazu können lokale Leserechte auf das Windows-Systemlog nötig sein.
Der Replayprüfer diagnostiziert allein aus Konvertierungsbelegen weiterhin
`historical_cause=undetermined`; die Standbyzuordnung stammt separat aus den
exportierten Systemereignissen. Kompakte, prüfsummengebundene Ergebnisse:
`artifacts/evaluation/deadline_overrun_audit_v1/summary.json`.
