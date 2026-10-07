# Plan-B-Abnahmetest mit neuer Auswahl bei jedem Start

```powershell
python -m tools.run_plan_b_variations
```

Jeder Start zieht zufällig **ein SVG zusammen mit seiner Beschreibung** aus
`artifacts/images_to_convert/samples` und der Beschreibungstabelle
`artifacts/images_to_convert/Finale_Wurzelformen_V3.xml`. Es gibt kein festes
Testmotiv und keinen festen Standard-Seed. Alle zugeordneten Aufgaben sind
wählbar, unabhängig von ihrer bisherigen Konvertierungsqualität.
SVGs ohne zugeordnete Beschreibung werden im Auswahlprotokoll ausgewiesen.
Bildspezifische Beschreibungen aus der Tabelle werden berücksichtigt.

Aus dieser Aufgabe entstehen genau 16 verschiedene SVGs und 16 veränderte
Beschreibungen: Skalierung ±6 %, Verschiebung horizontal/vertikal ±2,5 % der
Zeichenfläche und unterschiedliche Formulierungen. Die Beschreibung behält
ihre bisherigen Aussagen und ergänzt die passende relative Änderung;
konkrete Koordinaten werden dem Konverter nicht verraten. Ganze Motive werden
gemeinsam verändert; Lagebeziehungen zwischen ihren Bestandteilen bleiben erhalten.
Bei Motiven nahe am Rand kann eine kleine Änderung zu Abschneidung führen.

Die Referenzen werden verlustfrei als PNG rasterisiert. Der **echte CLI-Konverter**
erhält je Fall nur dieses Rasterbild und dessen Beschreibung, unter anonymem
Namen und im Modus `semantic-only`. Jeder Fall hat ein frisches Ausgabe- und
Eingabeverzeichnis. Referenz-SVGs werden nicht als Konvertereingabe übergeben.
Ein Audit-Hook im CLI-Unterprozess blockiert außerdem das Lesen fremder SVGs
(einschließlich Katalogvorlagen und Testreferenzen); erlaubt bleiben ausschließlich
die in diesem Fall selbst erzeugten SVGs. Jeder versuchte Vorlagenzugriff zählt
als Fehler, auch wenn der Konverter ihn intern abfängt. Das Protokoll steht in
`reference_access.json`.

## Verbindliche Abnahme

Alle 16 Fälle müssen die vorab festgelegten Grenzen bestehen:

| Messung | Grenze |
| --- | --- |
| Normalisierter mittlerer RGB-Quadratfehler | höchstens 0,01 |
| RGB-Quadratfehler im Vordergrund | höchstens 0,04 |
| Symmetrische Konturübereinstimmung | mindestens 0,72 |
| Vordergrund-Überlappung (IoU) | mindestens 0,85 |
| Intrinsische Bildgröße | identisch zur Eingabe |
| Vektorelemente / Pfadbefehle | höchstens 80 / 160 |
| Eingebettete Rasterbilder | keine |

Der Fehler wird durch `255²` normalisiert und über die drei Farbkanäle gemittelt.
Die Konturmetrik ist der Mittelwert von `exp(-Abstand)` zur jeweils nächsten
Gegenkontur, in Pixeln, mit Canny-Grenzen 50/140. Für die Vordergrundmaske dient
die mediane Randfarbe als Hintergrund; eine Kanalabweichung über 25 zählt als
Vordergrund. Vordergrundfehler und IoU verhindern, dass große leere Flächen
fehlende Motive verstecken. Diese generische Prüfung bewertet sichtbare
Rekonstruktionsqualität, keine vollständige sprachliche Semantik/OCR.

Ein fehlendes/unlesbares Ergebnis, Prozessfehler oder Timeout zählt als Fehler.
Die übrigen Fälle werden trotzdem abgearbeitet. Ein gutes Mittel über mehrere
Fälle kann einen schlechten Einzelfall nicht ausgleichen. Exitcode **0 bedeutet
16/16**, andernfalls endet der Test mit **1**. Ergebnisse im Fehlgeschlagen-Ordner
des Konverters werden ebenfalls unabhängig vermessen; dessen historische
Erfolgsmarkierung ersetzt die Abnahme nicht.

## Ergebnisse und Wiederholung

Jeder Start legt einen neuen Lauf unter `artifacts/evaluation/plan_b_variations`
an. Diese erzeugten Laufverzeichnisse sind in `.gitignore` ausgeschlossen und
bleiben lokal; CI lädt sie als Workflow-Artefakte hoch. Sie werden nicht als
Quelldateien ins Repository aufgenommen.
`manifest.json` enthält Auswahlpool, ausgewähltes SVG, Seed, Quell-Hashes,
16 Varianten und feste Qualitätsgrenzen. Die Ausgangsaufgabe liegt als
`source.svg` und `source_description.txt` bei. `report.json` wird nach jedem
Fall fortgeschrieben und enthält Einzelmetriken, Gründe und das Gesamtergebnis.
Pro Fall bleiben Konverterlog, Rastereingabe, Ergebnis-SVG und Vergleichsbilder
erhalten (`comparison.png`: Eingabe, Ergebnis, absolute Differenz).

Gezielt denselben Lauf wiederholen, auch wenn sich der ursprüngliche Pool ändert:

```powershell
python -m tools.run_plan_b_variations --svg PFAD/ZUM/LAUF/source.svg --description-file PFAD/ZUM/LAUF/source_description.txt --seed SEED_AUS_MANIFEST
```

Eine feste Auswahl per `--svg` ist nur eine ausdrückliche Wiederholung bzw.
gezielte Diagnose. Der Standardstart wählt immer neu. Gleiche zufällige
Auswahlen in aufeinanderfolgenden Starts sind möglich.

Eigene Aufgabenpools:

```powershell
python -m tools.run_plan_b_variations --svg-dir MEIN_SVG_ORDNER --descriptions-path MEINE_BESCHREIBUNGEN.xml
```

Alternativ kann jedes SVG seine Beschreibung in einer gleichnamigen `.txt`-Datei
haben; diese hat Vorrang vor der Tabelle. Die Tabelle unterstützt wie der
Konverter XML/CSV/TSV. `--timeout-seconds` (Standard 60) begrenzt jeden
Unterprozess, `--iterations` (Standard 64) steuert das Suchbudget.
`--output-dir` muss ein noch nicht vorhandenes Verzeichnis bezeichnen.

Der GitHub-Workflow **Plan B random task acceptance** startet diesen echten
Abnahmetest für Pull Requests, Pushes auf main/master/work und manuelle Starts.
Auch in CI wird bei jedem Start neu ausgewählt. Er bleibt bei Qualitätsfehlern
rot und lädt die Belege auch bei Fehlschlägen hoch. Die schnellen Tests in
`tests/detailtests/test_plan_b_variations.py` sichern Auswahl, Varianten,
Qualitätsmessung und Fehlerpfade ab; sie ersetzen den echten Abnahmelauf nicht.
