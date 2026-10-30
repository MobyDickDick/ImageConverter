# SEARCH-STRUCTURE-01: angeschnittene Elternkreise

Basis `7e6124bea`. [Umsetzung, Grenzen und Reproduktion](../../../docs/next_arbeitspaket_2026-10-30_clipped_parent.md).

| Echte CLI-Kohorte | Vorher | Finale Runtime |
| --- | --- | --- |
| Seed 853197, drei bekannte Randfehler, identische Rasterbytes | 0/3 | 3/3 |
| Derselbe Seed, vollständige Original-plus-16-Varianten-Kohorte | historisch 14/17 | 17/17 |
| Seed 618293, zusätzliche zwölf synthetische Kanten-/Eckfälle | nicht gemessen | 12/12 |

Suchseed 17, fünf Sekunden je Bild, unveränderte Qualitätsgrenzen. Alle
finalen Ausgaben wurden unabhängig anhand nativer Objekte, Konturen,
Zeichenreihenfolge sowie lokaler/globaler Rastermetriken erneut geprüft.
Die Referenz-SVGs sind für die Konvertierungsprozesse gesperrt.

`summary.json` enthält Eingabe-/Runtimehashes, die gepaarten drei Fälle und
alle 29 finalen CLI-Entscheidungen. Die drei Fälle sind Teil der 17 Varianten
und werden nicht zur Gesamtzahl addiert. Der erste vollständige Vorherlauf
hatte zusätzlich einen äußeren Timeout und keine vollständige Zugriffsevidenz;
seine gemeldeten 13/17 zählen nicht als vollständig geprüfte Baseline.
Ein explorativer 17/17-Lauf mit einer Änderung während der Ausführung ist
ebenfalls nicht die finale Abnahme. Die finale Runtime wurde über beide
vollständigen Kohorten hinweg anhand sämtlicher Produktionsdateihashes geprüft.

`checks.json` enthält die tatsächlichen Befehle, Exit-Codes, JUnit-Ergebnisse
und die bestehenden Laufzeitfehler. Der vollständige serielle Regressionsblock
endet mit **294 bestanden, drei Fehlern, einer Überspringung**, Exit 1.
Die drei alten Vier-Gruppen-Fälle scheitern auch mit unverändertem Basismodul:
**15/18 bestanden**, dieselben drei Fehler. Alle **30 neuen Tests** bestehen
innerhalb des größeren Blocks; das Kernprofil besteht separat **42/42**.
Ein zusätzlicher Versuch mit je einem OpenCV-/OpenBLAS-Thread wurde nach
denselben Fehlern beendet und zählt nicht als abgeschlossene Testabnahme.

Rohdaten bleiben lokal unter `.tmp/clipped-parent-*-20261030` und können mit
den dokumentierten Seeds neu erzeugt werden. Der neue CI-Job verwendet
temporäre Daten und bewahrt die Reproduktionsrezepte. Kein Archivpaar wurde
verändert. Vollständige Standardsuite, Python 3.10.20, allgemeine P0-Abnahme
und unabhängige reale Familienabnahme bleiben außerhalb dieses Teilabschlusses.
