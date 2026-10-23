# Gemeinsame Szenenauswahl und partielle Überdeckungen – GENERAL-SCENE-01

Branch: `codex/general-scene-fusion-2026-10-20`.
Messbaseline: `1f234c9c976cfd76a52448bf0c92a6bcdf80e993`.
Der schlanke Arbeitscommit baut auf `main` mit Stand `2cefc41b7` auf; dessen
Dateibaum ist mit der Messbaseline identisch.

Das in `open_tasks.md` als nächste Architekturarbeit bezeichnete Paket
ergänzt die vorhandenen getrennten und vollständig verschachtelten Szenen um
Detektorfusion und partielle Überdeckungen. Der ursprüngliche begrenzte
Kreis-/Rechteckumfang von GENERAL-SCENE-01 verwendet damit Instanzgruppen und
gemeinsame Szenenauswahl einschließlich alternativer Zeichenreihenfolgen.
Das ist keine Abnahme beliebiger Motive oder beliebiger Beschreibungssprache.

## Umsetzung

`imageCompositeConverterSceneFusion.py` führt die vorhandenen vollständigen
Vordergrund-/Farbgrenzen mit zwei ergänzenden analytischen Erkennern zusammen:
sichtbare Kreisbögen und sichtbare achsparallele Rechteckseiten. Kreisbögen
werden deterministisch gegen störende Überdeckungskanten geschätzt; mindestens
ein Halbkreis muss beobachtet sein. Rechtecke benötigen an allen vier Seiten
ausreichend außen sichtbare Unterstützung. Eine vollständig verdeckte Seite
wird nicht aus einer anderen Form oder einem gespeicherten Muster ergänzt.

Räumlich gleiche Vorschläge landen in derselben Instanzgruppe. Unterschiedliche
Formdeutungen bleiben Alternativen; die Herkunft der beteiligten Erkenner wird
in `primitive_scene_registration.scene_detectors` mitprotokolliert. Zusätzliche
Instanzgruppen dürfen nicht zugunsten eines guten globalen Pixelwerts entfallen.

Der aus dem bisherigen Flächenfit extrahierte `fit_scene_groups` ist der
gemeinsame native Szenenlöser. Bei Überdeckungen konkurrieren die möglichen
Zeichenreihenfolgen. Ein grober analytischer Farbrastervergleich priorisiert
sie; Annahme und Verfeinerung verwenden ausschließlich den echten SVG-Renderer
und die unveränderten globalen und lokalen Pixelgrenzen. Vorschlagsausdehnung
und Zahl der verfeinerten Hypothesen sind begrenzt; Erkennung, Auswahl und Fit
laufen unter dem vorhandenen überwachten Bildbudget.

Beschreibung und Geometrie müssen in Formarten, Anzahl und Beziehungen
übereinstimmen. Eine explizit getrennte dritte Form muss zu beiden anderen
disjunkt sein. Bei Kreisen bzw. gemischten Paaren wird die tatsächliche native
Schnittbedingung geprüft; eine Überlappung der Außenboxen allein genügt nicht.
Textanforderungen, widersprüchliche Negationen und nicht unterstützte
Überdeckungs-/Sprachbedingungen werden konservativ zurückgewiesen.

Der reguläre Anschluss bleibt `fit_primitive_scene` in der `semantic-only`-CLI.
Vorhandene erfolgreiche Kontur- und Flächenszenen behalten Vorrang. Der
historische Perception-IR-Merge wird nicht pauschal für beliebige andere
Detektoren umgestellt. Das optionale CNN bleibt unverändert optional.
Es gibt keine Rastereinbettung, Konturpfadausgabe oder bildnamenabhängige Regel.

## Nachweisverfahren

`tools.evaluate_fused_scene` erzeugt native Referenzszenen unabhängig von den
Produktionsdetektoren. Referenz-SVG-Zugriffe sind in den Konvertierungsworkern
gesperrt. Beide Vergleichsarme laufen durch dieselbe echte CLI mit Suchseed 17,
64 angeforderten Iterationen und fünf Sekunden Bildbudget ohne Verlängerung.
Der Verifikator verlangt zusätzlich den beobachteten isolierten Budgetvertrag
aus dem Runtime-Bericht. Die äußere Prozessgrenze des Messwerkzeugs beträgt
30 Sekunden.

Gespeicherte Ausgaben werden unabhängig erneut gerendert. Neben den bestehenden
Pixel-/Komplexitätsgrenzen werden Anzahl, native Formarten, Außenmaße mit
höchstens 2,5 Pixeln Abweichung und die korrekte Reihenfolge überdeckender
Objekte geprüft. Jede Referenzobjektregion besitzt eine zusätzliche Rasterprüfung.
Das Feld `parent` im generierten Inventar verlangt hierbei ausschließlich die
Zeichenreihenfolge; es behauptet bei Teilüberdeckung keine Verschachtelung.

Die zwölf Entwicklungsszenen mit Seed 20261020 wurden vor der Runtime-Änderung
eingefroren und liefern beim Elternstand 0/12 vollständige Abnahmen. Sie
enthalten Kreis-/Kreis-, Rechteck-/Rechteck- und beide gemischten Paare,
teilweise mit einer zusätzlichen getrennten Form. Die nachgelagerten Sätze
739821, 813795, 951327 und 627153 sowie die Varianten mit Seeds 289451, 108537,
435281 und 839475 sind nach den letzten Runtime-Korrekturen ausschließlich
Entwicklungsdaten. Eine zusätzliche Sprachprobe mit weißem Hintergrund bestand
zunächst 0/12: Die Fallnormalisierung ersetzt „ß“ durch „ss“, während der erste
neue Hintergrundausdruck noch „ß“ erwartete. Drei positive Regressionen decken
diese allgemeine Normalisierung ab; Geometrie und Qualitätsgrenzen bleiben gleich.
Der endgültige neue Prüfsatz verwendet Seed 862719, gedrehte Anordnungen,
umformulierte Beschreibungen und ausdrückliche weiße Hintergrundangaben.
Die endgültige erweiterte Vorlage verwendet Seed 593187. Beide wurden nach
dem letzten Runtime-Code-Freeze erzeugt; ihre Ergebnisse ändern keine Geometrie
oder Qualitätsgrenze.

Versioniert sind nur die kleinen Ergebniszusammenfassungen und Prüfzahlen unter
`artifacts/evaluation/fused_scene_v1/`. Die vollständigen 123 Nachweisdateien
mit Raster-/SVG-Paaren, Manifest und Runtime-Einzelmessungen bleiben lokal unter
`.tmp/fusion-full-evidence/`; zusätzlich liegen sie in
`.tmp/fusion-evidence-d73eb727c.zip`. Der ursprüngliche Commit ist im lokalen
Git-Bundle `.tmp/fusion-before-slim-d73eb727c.bundle` gesichert.

Der schlanke Commit enthält keine erzeugten PNGs, SVGs oder Rohmanifeste.
Die `.gitignore` verhindert ihre erneute versehentliche Aufnahme. Nach einem
frischen Clone sind die lokalen Rohdaten nicht vorhanden: Neue Szenen mit den
unten angegebenen CLI-Befehlen erzeugen, konvertieren und deren eigene Ausgaben
erneut prüfen. Die kompakte Zusammenfassung allein ist kein Ersatz für eine
unabhängige Raster-/SVG-Prüfung. CI lädt seinen eigenen vollständigen Lauf als
Artefakt hoch. Die synthetischen Szenen gehören nicht zum abgenommenen Katalog.

## Ergebnisse und Bestandsschutz

| Prüfgruppe | Eingefrorener Elternstand | Neuer Stand |
| --- | ---: | ---: |
| 12 eingefrorene Entwicklungsszenen | 0/12 | 12/12 |
| 12 neue finale Prüfszenen | 0/12 | 12/12 |
| Finale Prüfszenen unter neutralen Namen | – | 12/12, SVGs bytegleich |
| Neue erweiterte Vorlage | – | 17/17 |
| Bisherige gefüllte/verschachtelte Prüfszenen | 36/36 | 36/36, SVGs bytegleich |
| Neuer CI-Smoke, lokal ausgeführt | – | 6/6 |

Der mittlere normalisierte MSE sinkt in der Entwicklungsgruppe von
0,02716918 auf 0,00023542 und im neuen Prüfsatz von 0,02823335 auf 0,00019253.
Ein Erfolg verlangt zusätzlich sämtliche Objekt-/Regionsprüfungen.
Die Laufzeiten unter paralleler lokaler Testlast begründen keine allgemeine
Beschleunigungsquote. Ein entfernter CI-Lauf wurde nicht gestartet.

Die Vergleichsgrafik `comparison.png` ist im lokalen vollständigen Nachweis enthalten.

Alle **377 Archivpaare** und ihr Index bleiben hashgleich. Aus geschützten
Kopien erneut konvertiert bestehen **377/377** die bestehende absolute
Archiv-Pixelgrenze. Keine Archivbeschreibung aktiviert die Fusionsgrammatik;
kein Archivlauf wählt eine Primitive-Szenenregistrierung. Die Archivgrenze
ist keine Gleichheit mit jedem historischen Bestwert: 41 Neukonvertierungen
haben einen höheren `mean_delta2` als das gespeicherte beste SVG, wie bereits
beim vorigen Archivlauf. Gegenüber dessen Messwerten unterscheiden sich vier
Batchausgaben: `AC0413_S`, `AC0414_L` und `AC0421_S` geringfügig nach oben,
`AC0840_M` nach unten. Keiner dieser Fälle verwendet den neuen Szenenfit;
alle bestehen das Archivgate. Gespeicherte bessere Ausgaben bleiben erhalten.
Die 36 expliziten früheren Flächen-/Verschachtelungsszenen sind zusätzlich
vollständig erneut geprüft und gegenüber ihren Elternausgaben bytegleich.

Die abschließende betroffene Szenen-/Netz-/Plan-B-Regression besteht mit
**198 Tests**. Ein erster früherer Lauf hatte einen Fehler im vorhandenen
Worker-Umgebungstest; die einzelne Wiederholung mit temporären Dateien im
Workspace und beide späteren vollständigen gezielten Läufe bestehen.
Die Ursache des ersten Fehlers wurde nicht unabhängig bestimmt. Er wird
in `checks.json` als gesonderter fehlgeschlagener Versuch erhalten.

Die parallel gestartete Standardsuite schließt mit **3.648 bestandenen,
30 regulär übersprungenen und einem fehlgeschlagenen Test** ab. Der bestehende
Zwei-Sekunden-Test `test_blocked_real_inference_is_inside_the_process_deadline`
beobachtete im Gesamtlauf keinen Inferenz-Einstiegsmarker, obwohl die äußere
Zeitprüfung bestand. Die isolierte Wiederholung und die endgültige betroffene
198-Test-Regression bestehen ohne Änderung des Budgets oder der Prüfung.
Der fehlgeschlagene Versuch bleibt erhalten; die genaue Ursache des fehlenden
Inferenz-Einstiegs wurde nicht unabhängig bestimmt. Es wird keine vollständig grüne
Standardsuite behauptet.

Die Standardsuite wurde vor den letzten lokal begrenzten Beziehungs-/Sprach-
korrekturen gesammelt; die endgültigen betroffenen Module sind zusätzlich
in der 198-Test-Regression geprüft. Beide XML-Berichte decken zusammen alle
**3.689 aktuell gesammelten Test-IDs** ab, keine fehlt. Die drei ausdrücklich
herausgenommenen schweren Module wurden nicht zusätzlich gestartet. Alle
Prüfzahlen, XML-Prüfsummen und der Wiederholungslauf stehen in `checks.json`.

## Reproduktion

```powershell
.venv/Scripts/python.exe -m tools.evaluate_fused_scene --prepare .tmp/fused-inputs --seed 862719 --count 12 --rotate --paraphrase
.venv/Scripts/python.exe -m tools.evaluate_fused_scene --inputs .tmp/fused-inputs --output .tmp/fused-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_fused_scene --inputs .tmp/fused-inputs --output .tmp/fused-cli --verify-only --require-all
.venv/Scripts/python.exe -m tools.evaluate_fused_scene --prepare .tmp/fused-plan-b-inputs --seed 593187 --count 12 --rotate --paraphrase --variations
.venv/Scripts/python.exe -m tools.evaluate_fused_scene --inputs .tmp/fused-plan-b-inputs --output .tmp/fused-plan-b-cli --require-all
# Optional: vorhandenen vollstaendigen lokalen Nachweis pruefen
.venv/Scripts/python.exe -m tools.summarize_fused_scene_evaluation --verify-only
.venv/Scripts/python.exe -m pytest -q tests/test_scene_fusion.py tests/test_layered_scene_runtime.py tests/test_primitive_scene_runtime.py
```

Frische Läufe benötigen neue Ausgabeverzeichnisse. Der CI-Job
`fused-primitive-scenes` erzeugt sechs neue gedrehte Szenen mit Seed 871205,
konvertiert sie und überprüft die gespeicherten Ergebnisse erneut.

## Grenzen und Folgearbeit

Der nachgewiesene Überdeckungsumfang umfasst zwei bis drei einfarbig gefüllte,
unbeschriftete Kreise/achsparallele Rechtecke vor weißem Hintergrund mit klar
unterscheidbaren sichtbaren Farbregionen. Die vorherigen getrennten Kontur-
und gefüllten/verschachtelten Umfänge bleiben bestehen. Vollständig verdeckte
Rechteckseiten, stark verdeckte Kreisbögen, gleiche verdeckende Farben,
Überdeckung mit eigenen Konturen, kombinierte Verschachtelung/Teilüberdeckung,
freie Tiefenreihenfolge in Sprache, Text, Verläufe und weitere Formarten
besitzen keinen allgemeinen Rekonstruktionsnachweis.

GENERAL-SCENE-VISIBILITY-04 führt diese Erweiterungen als eigenen offenen
Folgeumfang. IDO-19/IDO-21, die produktive Netzabnahme und
SEARCH-DEADLINE-COMPAT behalten ihren bisherigen offenen Status.
