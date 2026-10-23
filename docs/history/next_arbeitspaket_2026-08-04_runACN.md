# Nächstes Arbeitspaket – Atomarer Workflow-Kontext Run ACN (2026-08-04)

Run ACN härtet die in Run ACM wiederhergestellte Kontextprüfung. Ein Aufrufer
konnte bislang nur die erwartete Run-ID oder nur den erwarteten Run-Versuch
übergeben. Ein solcher Teilkontext sah wie eine gebundene Prüfung aus, ließ den
Beleg aber weiterhin entlang der jeweils anderen Workflow-Dimension offen.

## 1) Erwarteten Kontext nur vollständig akzeptieren

`verification_errors(...)` behandelt Run-ID und Run-Attempt als atomaren
Kontext. Sobald einer der beiden Erwartungswerte gesetzt ist, muss auch der
andere gesetzt sein. Die lokale Bestandsprüfung bleibt kompatibel: Werden
bewusst keine Erwartungswerte angegeben, prüft der Helper weiterhin nur die im
Beleg enthaltene, selbstbeschreibende Identität.

## 2) Erwartungswerte validieren

Beide Erwartungswerte müssen positive Ganzzahlen sein; boolesche Werte werden
wie bei den Belegfeldern ausgeschlossen. Der Checker sammelt diese
Konfigurationsfehler zusammen mit etwaigen Belegabweichungen, damit CI-Aufrufer
alle Ursachen in einem Lauf diagnostizieren können.

## 3) Regressionstests

Direkte Helper-Tests decken sowohl einen unvollständigen Erwartungskontext als
auch nicht positive Run-Werte ab. Die bestehende Workflow-Prüfung stellt
weiterhin sicher, dass der produktive Aufrufer beide Parameter gemeinsam
übergibt.
