# Plan-B-Workbench

Die lokale Workbench sammelt Daten zur Verbesserung des Konverters:
Ein SVG wird in das unveränderte Original und 16 geometrische Varianten
überführt. Jede Variante wird verlustfrei gerastert und durch die echte
Konverter-CLI wieder als SVG rekonstruiert. Eingabe, Ergebnis und absolutes
Differenzbild stehen direkt nebeneinander.

## Start und Bedienung

1. `startWebServer.cmd` starten und in der Oberfläche **Plan-B-Workbench** öffnen.
   Standardadresse: `http://127.0.0.1:8766/workbench`.
   Alternativ beim geprüften Konvertierungsergebnis auf
   **Als erweiterte Plan-B-Aufgabe verwenden →** klicken: SVG und Beschreibung
   werden übernommen, die 17 Fälle vorbereitet und direkt geöffnet.
2. Ein SVG wählen: Es erscheint sofort als Vorschau bei der Dateiauswahl.
   Unter Windows bleibt der zuletzt verwendete Referenzordner unabhängig von
   Rasterbild, Sample-SVG und Speicherziel erhalten, auch nach Serverneustarts.
   Die Workbench sucht seine Beschreibung automatisch anhand des Dateinamens,
   einschliesslich Zusätzen wie `_L` oder `_PlanB`. Verwendet werden zuerst
   passende `.txt`-Begleitdateien unter `artifacts/samples`, dann
   `artifacts/images_to_convert/Finale_Wurzelformen_V3.xml` und als weitere
   Quelle `artifacts/descriptions/Finale_Wurzelformen_V3.xml`. Bildspezifische
   Einträge haben Vorrang vor allgemeinen Familienbeschreibungen.
   Funddatei und Schlüssel erscheinen unter dem editierbaren Beschreibungsfeld.
   Bei fehlendem Treffer bleibt die SVG-Vorschau verfügbar; eine eigenständige
   Beschreibung von Formen, Farben und Lagebeziehungen eingeben.
   Keine numerischen SVG-Parameter abschreiben.
   Optional einen früheren Seed angeben; sonst entsteht ein neuer Zufallsseed.
3. **Varianten vorbereiten** erzeugt Original und 16 verschiedene Raster.
   Bis hier läuft noch keine Rückkonvertierung. Die aktuelle Variante verändert
   das gesamte Motiv: Skalierung ±6 %, Lage horizontal/vertikal ±2,5 % der
   Zeichenfläche. Die Beschreibung ergänzt die passende relative Änderung.
   Teilobjekte werden in dieser ersten Version nicht unabhängig verschoben.
4. Einzelne Fälle auswählen oder **Alle 17 Fälle ausführen** starten.
   Iterationen und Zeitlimit gelten je Fall. Während des Laufs erscheinen
   Fortschritt und abgeschlossene Ergebnisse. **Lauf abbrechen** beendet den
   Prozessbaum; abgeschlossene Ergebnisse bleiben bestehen.
   Oberhalb der Aufgaben zeigt **Ein Vorgang läuft** den aktiven Vorgang mit
   **Diesen Vorgang abbrechen** an. Das funktioniert auch, wenn eine andere
   Plan-B-Aufgabe geöffnet ist oder die normale Bildkonvertierung läuft.
5. Einen Fallnamen anklicken, Vergleich und Messwerte prüfen und Beobachtungen
   beziehungsweise unterschiedliche Lösungshypothesen als Notiz speichern.
6. JSON-Bericht, CSV-Messdaten oder das gesamte Datenpaket als ZIP herunterladen.
   Gespeicherte Aufgaben lassen sich nach einem Serverneustart wieder öffnen.

Eigenständige SVGs bis 2 MB, 4096 Pixel pro Seite und insgesamt 4 Megapixel
werden angenommen. Aktive Inhalte, eingebettete Bilder und externe Ressourcen
werden abgewiesen. Die lokale Oberfläche verwendet dieselben Host- und
Herkunftsprüfungen wie die Bildkonvertierung. Eine GUI-Konvertierung und ein
Workbench-Batch laufen nicht gleichzeitig im selben Server.

## Diagnose und Abnahme

Die Workbench ist eine Diagnoseoberfläche: Anders als die
[verbindliche Plan-B-Abnahme](plan_b_variation_acceptance.md) lassen sich
Varianten auch bei einem fehlerhaften Original ausführen. Es findet keine
Auswahl eines anderen Motivs statt. Die bestehende Abnahme wird nicht verändert.

Jeder Fall verwendet weiterhin `semantic-only`, einen anonymen Fallnamen,
Rasterbild plus Beschreibung und den vorhandenen Audit-Hook gegen das Lesen
fremder SVG-Vorlagen. Die Referenz dient ausschliesslich der Rasterisierung
und unabhängigen Auswertung, nicht als Rekonstruktionsvorlage.

Die bestehenden festen Pixel-, Grössen- und Komplexitätsgrenzen bleiben
unverändert. „Bestanden“ bestätigt diese generischen Prüfungen; insbesondere
kleine fehlende Objekte, Textinhalt und vollständige Semantik benötigen
zusätzliche fachliche Sichtprüfung. Qualitätsfehler und technische Fehler
(Timeout, fehlende Ausgabe, Vorlagenzugriff usw.) werden getrennt gezählt.

Die Tabelle zeigt das **letzte abgeschlossene Ergebnis je Fall**. Ein erneuter
Versuch überschreibt die vorherigen Artefakte nicht. Die Zusammenfassung kann
Ergebnisse verschiedener Versuche enthalten und ersetzt daher keinen
gemeinsamen verbindlichen 17-Fälle-Abnahmelauf. Die CSV enthält dagegen jede
abgeschlossene Messung aller Versuche, jeweils mit Versuch und Budget.
Ein erfolgreicher Diagnoseprozess hat Exitcode 0, auch wenn Qualitätsfehler
vorliegen; die Abnahmeentscheidung steht in den Einzelergebnissen.

## Gesicherte Daten

Unter `artifacts/gui/workbench/<Lauf-ID>/` bleiben erhalten:

- Original-SVG, Beschreibung und Quellhash, Variantenparameter und genauer Seed.
- Referenz-SVGs, verschiedene Rastereingaben, deren Hashes und Beschreibungen.
- Pro Versuch: Budget, Suchseed, echte CLI-Befehle, Ergebnis-SVGs und Hashes,
  Qualitätsmessungen, Fehlergründe, Laufzeit, Differenzbilder, Suchprotokolle,
  Debugdateien und Audit-Berichte.
- Git-Revision und Hinweis auf lokale Änderungen; Python-Version,
  Paketversionen und Hash der Python-Quelldateien. Jeder neu ausgeführte Fall
  erhält ebenfalls den aktuellen Softwarefingerabdruck.
- Fallnotizen und Status bei Abbruch oder Serverneustart.

Die Quelldateihashes kennzeichnen lokale Änderungen, archivieren aber nicht den
gesamten Softwarestand. Für genaue Wiederholungen den Code unverändert halten
oder dessen Stand zusätzlich sichern. Die Oberfläche speichert auch grosse
Seeds verlustfrei. Quellen und ältere Versuche werden nicht automatisch gelöscht;
das ZIP kann deshalb mit vielen Wiederholungen deutlich wachsen.

Der JSON-Bericht verwendet das eigenständige Schema `plan_b_workbench_v1`.
Er ist kein Ersatz für die Abnahmeberichte des bestehenden CI-Workflows und
erstellt keine GitHub-Issues oder automatischen Algorithmusänderungen.
Die fachliche Nachbearbeitung folgt dem
[Plan-B-Lernworkflow](plan_b_learning_workflow.md).

## Ohne Browser

Vorbereiten, anschliessend alle oder einzelne Fälle ausführen:

```powershell
.venv/Scripts/python.exe -m tools.plan_b_workbench --svg MOTIV.svg --description-file BESCHREIBUNG.txt --seed 42 --run-dir .tmp/meine-plan-b-aufgabe
.venv/Scripts/python.exe -m tools.plan_b_workbench --run-dir .tmp/meine-plan-b-aufgabe --cases all --iterations 64 --timeout-seconds 60
.venv/Scripts/python.exe -m tools.plan_b_workbench --run-dir .tmp/meine-plan-b-aufgabe --cases probe_01 probe_07
```

Der Vorbereitungsordner muss neu sein. Für Wiederholungen wird derselbe
vorbereitete Ordner verwendet; jeder Aufruf erzeugt einen eigenen Versuch.
Der Seed gilt für die Varianten und explizit für die Konvertersuche.

## Prüfung vom 12.11.2026

87 gezielte Tests für Workbench, bestehende GUI und Plan-B-Varianten bestehen.
Sie prüfen unter anderem verschiedene Raster, reproduzierbare Seeds, erhaltene
Fehlversuche, Varianten nach Originalfehler, partielle Ergebnisse, Abbruch des
Prozessbaums, Wiederöffnung, Export und Pfad-/Herkunftsschutz.
Ein tatsächlicher Browserlauf mit einem grünen Kreis (Seed 64217,
vier Iterationen, 30 Sekunden je Fall) besteht Original und alle 16 Varianten
über die echte CLI und die unveränderten unabhängigen Qualitätsgrenzen.
Die einzelne Wiederholung von `probe_01` liefert bytegleiche Eingabe und
Ausgabe, während das ältere Ergebnis erhalten bleibt. Der Audit-Hook
protokolliert bei allen diesen Versuchen keine fremden SVG-Zugriffe.
Das ist ein Funktionsnachweis der Workbench, kein allgemeiner Qualitätsnachweis
für beliebige SVG-Motive.
