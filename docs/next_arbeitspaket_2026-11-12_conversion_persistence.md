# CONVERSION-PERSISTENCE-01: Ergebnisse und Fortschritt konsistent sichern

Das nach CONVERSION-POWER-01 priorisierte Betriebspaket aus dem
[Katalogaudit](catalog_search_followup_2026-11-11.md#priorisierte-konsequenzen)
ist am 12.11.2026 umgesetzt. Es korrigiert die dort belegten verspäteten
Fehler-Checkpoints, überschriebenen Laufübersichten und veralteten Fehlerwerte
nach einer SVG-Nachoptimierung. Es erweitert noch keine Formgrammatik.

## Zustände und unveränderliche Belege

Jeder `convertRange`-Aufruf erhält eine neue Laufkennung, auch bei expliziter
Checkpoint-Wiederaufnahme. Unter `reports/runs/<run_id>/` liegen die Herkunft
in `run.json`, inhaltsadressierte Original-/SVG-/Beschreibungs-/Protokollobjekte
und unveränderliche Revisionen. Ein späterer Aufruf überschreibt diesen Lauf
nicht. `latest_checkpoint.json` wird nur während des betreffenden Aufrufs
fortgeschrieben. Wiederaufnahme nennt den Ursprungslauf separat.

`reports/conversion_checkpoint.json` ist der atomar ersetzte Einstiegspunkt:
`result_map_path`, `failures_path`, `reports_path` und
`completion_manifest_path` verweisen auf dieselbe vollständig geschriebene
Revision. Dateien innerhalb dieser Revision werden anschließend nicht geändert.
Alle referenzierten Originale und SVGs sind als eigene, hashgebundene Kopien
gesichert. Identische Objekte werden innerhalb eines Laufs einmal gespeichert.
Der Checkpointvertrag heißt `conversion_checkpoint_v2`: Die Ergebnisübersicht
referenziert hashgebundene Ergebniszeilen, damit große Suchhistorien nicht in
jeder folgenden Revision erneut gespeichert werden.
`loadConversionCheckpointResultMapImpl` prüft Index- und Zeilenhashes und liefert
weiterhin vollständige Ergebniszeilen; alte vollständige v1-Übersichten bleiben
lesbar. `attempt_reports_path` sichert außerdem die pro Bildversuch vorhandenen
Worker-, Timing-, Deadline- und Komponentenberichte vor dem nächsten Versuch.
Die bisherigen Dateien direkt unter `reports/` bleiben kompatible aktuelle
Ansichten; konsistente Leser folgen dem Checkpoint. Diese einzelnen Ansichten
bilden für sich keine Transaktion über mehrere Dateien.

Initial- und Qualitätsdurchläufe sichern vor Beginn jedes Bildversuchs `started`
samt `active_filename`; anschließend auch `completed`, `failed`, `skipped`
oder `interrupted`. `KeyboardInterrupt`, `SystemExit` und reguläre Ausnahmen
lassen einen Abschlusszustand zurück und werden weitergereicht. Insbesondere
führt der alte Fehlerzweig nicht mehr am Checkpoint vorbei. Die Fehler-CSV ist
bereits vor Beginn des nächsten Bildes aktuell. Fehler während der nachfolgenden
Batchfinalisierung werden ebenfalls gespeichert. Die Zufallsstartwerte werden
auch beim Abbruch zurückgesetzt.

CSV-Aktualisierungen verwenden ebenfalls temporäre Nachbardateien, Flush,
`fsync` und atomare Ersetzung. Ein fehlgeschlagener Revisionsschreibvorgang
kann unreferenzierte neue Dateien hinterlassen; der alte globale Checkpoint
verweist weiterhin auf seinen vollständigen Stand. Ein harter Prozessabbruch
oder Stromverlust führt keinen Python-Abschlusscode aus: Dann bleibt der
zuletzt gesicherte Startzustand sichtbar und der Versuch muss neu eingeplant
werden. Es gibt keine Behauptung einer vollständigen Hardware-Stromausfallabnahme.

Vor dem ersten Überschreiben eines vorhandenen Altstands werden dessen noch
verfügbare Berichte und referenzierte SVGs in einen separaten Legacy-Lauf
kopiert. Fehlende historische Herkunft wird nicht nachträglich erfunden;
solche Zeilen sind `unverified`. Bereits früher überschriebene Läufe können
dadurch nicht wiederhergestellt werden.

## SVG, Messwerte und Freigabe

Ergebniszeilen binden ihre Messwerte an den SHA-256 der tatsächlich ausgegebenen
SVG-Bytes und des Originalbildes. Die Archivierung prüft diese Bindung erneut.
Abweichungen heißen `artifact_mismatch` und erhalten keine Modellfreigabe.
Bei der Finalisierung in den vorhandenen Fehlerordner verschobene SVGs bleiben
mit ihren Messwerten archiviert. Zusätzliche Ablehnung durch die Finalisierung
setzt `search_satisfactory` ausdrücklich zurück.

Nach einer Vektornachoptimierung oder Rückkehr zu einer anderen früheren SVG
wird `best_error` am ausgewählten SVG als mittlerer absoluter Kanalfehler
neu gemessen. `best_error_metric=mean_absolute_error` kennzeichnet diesen Wert;
`optimizer_best_error` hält den früheren Fit-Rückgabewert separat fest.
Unveränderte Fit-Ergebnisse behalten ihre modusabhängige Optimierungsmetrik,
gekennzeichnet als `optimizer_objective`. `current_svg_mae`, `mean_delta2`,
Raummetriken und der Freigabestatus beziehen sich auf die ausgewählte Ausgabe.
Der alte Optimierungswert ist keine Qualitätsmessung einer ersetzten SVG.

Die Bestlisten-CSV zeigt `validated` bzw. `draft`, statt ein leeres Statusfeld
zu schreiben. Die bestehenden pixel- und modellbezogenen Prüfungen bleiben
erforderlich. Ein Pixelpass allein wird nicht zu einer Modellfreigabe.
`processed_result_count` zählt gespeicherte Ergebnisse; `successful_count`
und `validated_count` zählen ausdrücklich bestätigte Ergebnisse, `draft_count`
die übrigen. Das ist eine bewusste Präzisierung der früheren Bedeutung von
`successful_count`, das alle gespeicherten Ergebnisse zählte. Technische und
fachliche Fehler bleiben separat; `pending_count`/`execution_status` machen
vorzeitig beendete Bereichsläufe kenntlich.

Explizites `ICC_RESUME_FROM_CHECKPOINT=1` im Standardmodus prüft archivierte
Objekthashes und die aktuellen Original-/Beschreibungsdateien, bevor die exakten
SVG-Bytes wiederhergestellt werden. Veränderte oder beschädigte Eingaben,
fehlende Bindungen und Versuche ohne Ergebnis werden neu berechnet.
`semantic-only` liest weiterhin keine früheren SVGs zur Konvertierung.
Die Sicherung ist kein zusätzlicher Kandidateneingang und kein Strategielernen.

## Abnahme und Grenzen

Reproduktionsbefehle, Testergebnisse und Dateihashes stehen im
[Evidenzverzeichnis](../artifacts/evaluation/conversion_persistence_v1/README.md).
Die Prüfungen umfassen absichtlich fehlschlagende Schreibvorgänge,
Beschädigung/Änderung von Eingaben und Archivobjekten, beide Bilddurchläufe,
Fehler vor dem nächsten Bild, Abbrüche am öffentlichen Bereichseinstieg,
aktuelle Nachoptimierungsmetriken und zwei echte überwachte CLI-Aufrufe im
gleichen Ausgabeordner. Die alten Laufdateien bleiben beim zweiten Aufruf
bytegleich; die produktive Elternaufsicht startet weiterhin keinen Renderer.

Ein Ubuntu-/Windows-CI-Job ist ergänzt; dessen erster GitHub-Lauf steht noch
aus. Die lokale Abnahme erfolgte unter Windows: 160/160 gezielte Regressionen,
28/28 Prozessaufsichts-/Timingprüfungen einschließlich der zwei echten CLI-Läufe
und 42/42 Kerntests, jeweils ohne Überspringung. Die Testgruppen überschneiden
sich teilweise und werden nicht zu einer scheinbar unabhängigen Gesamtzahl
addiert. Kein neuer vollständiger
Kataloglauf, kein neuer realer Qualitätsgewinn und keine Standby-/Stromausfall-
Langzeitprüfung sind Bestandteil dieser Abnahme. Gleichzeitige Aufrufe im
gleichen Ausgabeordner werden durch dieses Paket nicht koordiniert; dafür
sind getrennte Ausgabeordner zu verwenden. Die Revisionen sparen wiederholte
SVG-Kopien, benötigen aber zusätzlichen Speicher für die Fortschrittshistorie.

## Nächstes dokumentiertes Paket: FALLBACK-STRUCTURE-01

Für die gewünschte flexiblere Konvertierung bleibt Punkt 3 des jüngsten Audits
die fachliche Hauptarbeit. Der tatsächlich häufig verwendete
`native_svg_continuation`-Pfad in `imageCompositeConverterVectorPolish.py`
verändert Platzierung, Skalierung, Konturbreiten und Farben vorhandener
Elemente. Die sechs Suchstrategien allein können daraus weder fehlende
Pfeilspitzen noch Kreuzlinien erzeugen. Die gemeinsame Struktursuche hat
leistungsfähigere Operationen, wird von den realen Katalogbeschreibungen in den
beiden Audits aber nicht erreicht.

Das nächste Paket soll deshalb begrenzt und messbar diesen Fallback erweitern:

1. Eine kleine Entwicklungsgruppe aus den gesicherten Auditfehlern vor der
   Runtimeänderung einfrieren: Originale, Beschreibungen, alte SVGs, Budgets,
   lokale fehlende Merkmale und Hashes. Bekannte Auditfälle sind Entwicklung,
   keine neuen unabhängigen Familien.
2. Mindestens zwei Hypothesen vergleichen: vollständige alternative native
   Konstruktionen mit wechselbaren Grundformen sowie aus unerklärten
   Originalregionen ergänzte Linien-/Liniengruppen. Vorhandene gemeinsame
   Operatoren möglichst wiederverwenden; keine Bild-ID- oder Familienweichen.
3. Unterschiedliche Objektarten/-zahlen und Kandidatenherkunft protokollieren.
   Konstruktionen unter demselben gesamten Bildbudget wie den heutigen
   Fallback vergleichen; keine zusätzliche Zeit als scheinbaren Strukturgewinn
   ausgeben. Kleine Bildgruppen unmittelbar auswerten.
4. Fehlende Linien/Objekte lokal prüfen, damit eine passende Hintergrundfläche
   sie nicht verdeckt. Positive und beschädigte negative Gegenproben sowie
   unveränderte Raster-/Objekt-/Beschreibungsprüfungen sind erforderlich.
   Pixelpass-Entwürfe bleiben bis zur fachlichen Prüfung Entwürfe.
5. Erst anschließend getrennte neue reale Familien vor Entwicklung markieren
   und sperren. Bekannte Verbesserungen, Varianten und neue Familien getrennt
   ausweisen. SEARCH-STRUCTURE-01 und GENERAL-SCENE-REAL-05 bleiben bis zu
   ihrer jeweiligen vollständigen Abnahme offen.
