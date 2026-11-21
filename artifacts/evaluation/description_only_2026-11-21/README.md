# Beschreibung verbindlich, zweite Rekonstruktion entfernt

Stand: 21. November 2026. Die Beschreibung bestimmt die erlaubten Elemente. Die
Bildmessung darf Position, Grösse, Farbe und andere Parameter dieser Elemente
bestimmen. Eine schlechte Rasterübereinstimmung erlaubt keine weiteren Elemente.

## Umsetzung

- GUI-Nachlauf und native Nachsuche beim CLI-Speichern und bei Vorlagen entfernt.
- Keine automatische Ersatzvorlage, keine wahrnehmungsbasierte zusätzliche
  Geometry-IR und keine generische Raster-Panel-/Element-Ersatzkonstruktion.
- Die Beschreibung gilt immer als vollständiges erkanntes Inventar. Die volle
  Prüfung gilt auch für fehlgeschlagene Dateien, Renderfehler und Vorschauen.
  Nicht inventarisierbare Kurvenpfade verschwinden nicht mehr aus der Zählung.
  SVG-Referenzen und eingebettete Bilder können die Prüfung nicht umgehen.
- Eine Vorlage mit abweichendem Inventar wird vor der Anpassung zurückgewiesen.
  Eine passende Vorlage darf als Ganzes ausgerichtet werden; ihre Elemente
  werden dabei erhalten. Optionale Veränderungen nur zur Erzeugung anderer
  Ausgabebytes werden nicht mehr angewendet.
- Fehlerpfade erzeugen weder eingebettete Originalbilder noch weisse
  Platzhalterrechtecke als SVG-Ergebnis. Protokolle und Diagnosedateien bleiben.
- Wiederholungen mit vorhandenem Ergebnis speichern `attempt_comparison` mit
  Geometriegleichheit, Rastergleichheit, Vordergrundähnlichkeit und beiden Seeds.
  Das gilt durch die Verknüpfung der Aufträge auch für den Katalogdienst.
  Identische und mindestens 99 % ähnliche Fehlversuche werden im Status benannt.
  Ein fehlendes Ergebnis wird weiterhin als Fehlschlag behandelt.

Die alten Struktur-Suchmodule bleiben für isolierte Forschungs-/Hilfstests
vorhanden. Die produktiven Konvertierungspfade rufen sie nicht mehr auf.
Historische Ergebnisse und die vom Benutzer bearbeiteten Beschreibungen und
Sample-Dateien wurden für diese Änderung nicht überschrieben.

## Historischer Nachweis: allgemeine Verschiedenheit widerlegt

Der Audit erfasst gespeicherte GUI-Fehler und alle Verzeichnisse
`converted_svg_failed` unter `artifacts`, einschliesslich früherer Prüfstände.
Die Bestandsaufnahme fand vor den neuen isolierten Prüfläufen statt. Es handelt
sich um gespeicherte Endartefakte, nicht um sämtliche internen Suchkandidaten.

| Messung | Ergebnis |
| --- | ---: |
| Gefundene Fehler-SVGs | 1157 |
| Davon eigenständige, gerenderte Vektoren | 901 |
| Wegen eingebetteter Rasterbilder/Foreign Objects nicht gerendert | 256 |
| Weitere GUI-Fehler ohne gespeichertes Ergebnis | 86 |
| Vergleichspaare mit gleichen Eingabepixeln und gleichem Beschreibungstext | 950 |
| Davon identische SVG-Dateien | 291 |
| Davon identische SVG-Dateien trotz verschiedener Seeds | 283 |
| Identische Raster bei 96 × 96 Pixeln | 296 |
| Vordergrundähnlichkeit mindestens 99 %, einschliesslich identischer Paare | 583 |
| Raster-Duplikatgruppen im gesamten gerenderten Bestand | 76 |

Byteidentische SVGs sind ein unmittelbares Gegenbeispiel zur Behauptung,
alle fehlgeschlagenen Konvertierungen seien verschieden. Selbst unterschiedliche
Geometrien oder Bildinhalte wären noch kein Nachweis nützlicher Eigenleistung
oder einer Generalisierung auf unbekannte Bilder. Ein solcher Mehrwertnachweis
wurde mit dieser Änderung nicht erbracht.

Beispiel aus den lokalen Aufträgen: `GE9005_7S.jpg`, Seeds
`7977751317065944907` und `4228213290194050918`, Aufträge
`00a09aca95f04796b6941c0537c8596a` und `aadf0b1fe45c4181b017dd2fb92156f4`.
Beide Ergebnisdateien haben SHA-256
`7bbbfec71f4a2ebffff133a6b43d1e4d2381e9b5d3e28d83bc812f6753394602`.

Für den visuellen Vergleich wird jedes SVG auf 96 × 96 RGB-Pixel gerendert.
Die Ähnlichkeit ist 1 minus der mittleren absoluten RGB-Abweichung, geteilt
durch 255, auf der Vereinigung der Vordergrundpixel beider Ergebnisse
(mindestens ein Kanal unter 245). Weisser Hintergrund verdünnt den Unterschied
dadurch nicht. Der Wert ist eine offengelegte Bildmetrik, keine menschliche
Wahrnehmungsbewertung. Kleine Unterschiede können durch die Rasterauflösung
verschwinden; deshalb wird zusätzlich die exakte Dateigleichheit ausgewiesen.
Die eigene GUI-Ergebnisdatei und ihre CLI-Kopie werden nicht als zwei
Wiederholungen desselben Versuchs gezählt. Die Paarzahlen sind keine Zahl
unabhängiger Bilder.

Lokale Einzelbelege: [vollständiger Audit](history_audit/report.json),
[Vergleichsbilder](history_audit/comparison.png).
Der kompakte [Prüfstand](summary.json) bleibt versionierbar.

Reproduktion im Projektverzeichnis:

```powershell
.venv/Scripts/python.exe tools/audit_failed_conversion_diversity.py --output artifacts/evaluation/description_only_repeat
.venv/Scripts/python.exe tools/evaluate_description_only.py --output artifacts/evaluation/description_only_fresh
```

Eine erneute Bestandsaufnahme kann wegen inzwischen hinzugekommener Aufträge
andere Anzahlen ergeben. Der Audit verändert keine bestehenden Konvertierungen.

## Frische CLI-Läufe und Grenzen

Acht isolierte Läufe verwenden neutrale Dateinamen, zwei Seeds und kopierte
Eingaben. [Befehle, Beschreibungen und Ergebnisse](final_runs/results.json)
bleiben lokal verfügbar. Kein Lauf startet die zweite Nachsuche. Nur die zwei
Läufe des unterstützten Kreises erzeugen ein erfolgreiches SVG; beide bestehen
die Inventarprüfung. Die übrigen sechs melden einen Fehler ohne Ersatz-SVG.

Die Wortwahl „Ein grauer Kreis mit dunkelgrauem Rand“ funktioniert für das
unabhängig erzeugte Kreisbild. „Ein grauer Kreis mit dunklem Rand“ scheitert
derzeit bereits an der begrenzten Modellgrammatik. Das ist eine Grenze des
Programms, kein Qualitätsmangel dieser verständlichen Beschreibung.

Die aufgelöste aktuelle Beschreibung von `AC0201_M` beschreibt tatsächlich ein
motorgetriebenes Zweiwegventil mit Kelle und Griff. Die Grundbeschreibung
„Kompressor grau nach oben“ ist dafür nicht die effektive Beschreibung. Das
aktuelle Inventar versteht diese zusammengesetzte Formulierung nicht hinreichend.
Auch eine zusätzliche experimentelle Beschreibung mit explizitem Kreis, Linie
und zwei Dreiecken erreicht noch keine passende Rekonstruktion. Es wurde keine
erfolgreiche Ventilkonvertierung behauptet und keine Katalogbeschreibung geändert.

Der Parser versteht keine beliebige natürliche Sprache und liefert keinen
allgemeinen Beweis, jeden unbekannten Gegenstand oder jede Beziehung zu erkennen.
Die geschlossene Inventarprüfung sichert die unterstützten erkannten Formtypen;
eine universelle Sprachinterpretation ist damit nicht gelöst. Insbesondere
komplexe zusammengesetzte Symbole können nun häufiger zurückgewiesen werden.
Das ist die sichtbare Konsequenz davon, fehlende Beschreibungsauswertung nicht
mehr durch beliebige Rasterfragmente zu ersetzen.

Die ersten beiden lokalen Sondierungsverzeichnisse (`fresh_runs` und
`fresh_runs_verified`) sind Zwischenstände: Der erste verwendete zunächst ein
falsches Tabellenformat, der zweite prüfte die noch zu enge Kreisformulierung.
Massgeblich sind ausschliesslich `final_runs` und der ausgewiesene historische
Snapshot. Diese Zwischenstände wurden nicht als erfolgreiche Prüfung gezählt.

## Abschlussprüfung

346 Tests bestanden, ein Test ausdrücklich ausgenommen. Abgedeckt sind unter
anderem CLI-Artefakte und Fehlerpfade, GUI, Vorschauen, Vorlagen, Seed-Verhalten,
Katalogwiederholungen, Inventarprüfung und die Erkennung identischer Ergebnisse.
[Prüfmetadaten](checks.json), [lokales Abschlussprotokoll](final_tests.log).
Die Nullprüfung für neue Bild-ID-Sonderfälle und `git diff --check` bestehen.

Der ausgenommene bestehende Test
`test_stop_during_real_refresh_kills_child_and_preserves_last_report` scheiterte
im erweiterten Vorlauf am Beenden eines Windows-Kindprozesses: `taskkill` konnte
in der eingeschränkten Umgebung den Prozess nicht beenden; anschliessend lief
`process.wait(timeout=15)` ab. Er wurde nicht als bestanden gezählt. Auch der
Zugriff auf den laufenden lokalen Webserver per Socket war hier gesperrt
(`WinError 10013`). Der laufende Server wurde deshalb nicht neu gestartet.
Zum Aktivieren nach laufenden Arbeiten `stopWebServer.cmd`, danach
`startWebServer.cmd` ausführen und die Browserseite neu laden.
