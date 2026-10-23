# Reale Szenenübertragung: zwei negative Gegenproben

Begrenzte Untersuchung **GENERAL-SCENE-REAL-TRANSFER-08** innerhalb von
**GENERAL-SCENE-REAL-05**. Ausgangsstand `8b4b2f18f`, Branch
`codex/general-scene-real-holdouts-2026-10-22`.

## Ergebnis

Die positive Übertragungsabnahme ist **nicht bestanden: 0/2**. Der gemeinsame
Szenenweg übernimmt die beiden neuen Zusammensetzungen nicht. Der Algorithmus
wurde vor, zwischen und nach den Versuchen nicht verändert. Genau ein Versuch
je Original; keine nachträgliche Anpassung von Beschreibung, Objektmarkierung
oder Qualitätsgrenzen. Die Untersuchung ist abgeschlossen;
GENERAL-SCENE-REAL-05 bleibt offen.

| Original und Zusammensetzung | Native Prüfung | Normierte MSE | Kantenabgleich | Vordergrund-IoU | Gemessene Versuchszeit |
| --- | --- | ---: | ---: | ---: | ---: |
| GE0018: überlappendes gerundetes Rechteckkreuz in Verlaufsscheibe | durchgefallen | 0,030006 | 0,142071 | 0,785921 | 5,031 s |
| GE0307: vier getrennte umrandete Flaggenfelder in Verlaufsscheibe | durchgefallen | 0,070807 | 0,341890 | 0,919324 | 3,781 s |

Unveränderte Grenzen: MSE ≤ 0,01, Vordergrund-MSE ≤ 0,04, Kantenabgleich ≥ 0,72,
Vordergrund-IoU ≥ 0,85. Zusätzlich native Objektzahl/-art, markierte Boxen mit
höchstens 2,5 Pixel Abweichung und lokale Regionsprüfungen wie in den bisherigen
Szenenpaketen. Beide SVGs scheitern bereits mit `non_native_scene_definition`;
die weiteren Pixel-/Regionsfehler bleiben im Bericht. Hoher IoU allein genügt
nicht. Beide CLI-Prozesse enden im regulären Batchbetrieb mit Exit 0; das ist
kein Qualitätssignal.

Die Versuchszeit aus `run_case` enthält Prozessstart, Konvertierung und die erste
Pixel-/Debugnachprüfung. Die späteren zusätzlichen Objekt-/Regionsprüfungen
sind darin nicht enthalten; dieser Wert ist keine reine CLI-Prozesszeit.

Je Versuch: Seed 17, 64 angeforderte Iterationen, festes überwachtes Bildbudget
5 Sekunden, äußerer Notabbruch 30 Sekunden. Die interne Suchtelemetrie endet nach 2,203
bzw. 1,453 Sekunden mit `supported_models_exhausted` und null adaptiven
Suchauswertungen. Die gesonderten Aufsichtsberichte messen 3,719 bzw. 2,735
Sekunden und enden mit `completed`. Kein Timeout und keine Budgetverlängerung.

## Auswahl und Grenzen

Original-JPEGs, eigenständige Beschreibungen und Objektboxen wurden vor dem
ersten Lauf in `config/real_scene_transfer_families.json` fixiert und über
Prüfsummen an den Runtime-Stand gebunden. Neutrale Namen `real_00.png` und
`real_01.png` enthalten exakt die verlustfrei dekodierten Originalpixel.
Die Worker erhalten Raster und Beschreibung; beide Vektorzugriffswächter
melden keine Zugriffe.

Der implementierende Agent markierte vergrößerte Originalpixel, ohne
Detektorvorschläge oder Referenz-/Ergebnis-SVG. Kein unabhängiger menschlicher
Annotationsaudit. Beide Originale gehören zum historischen Katalog. Die Suche
fand keine gezielte Runtime-Entwicklung oder annotierte Familienabnahme dieser
Zusammensetzungen; Abwesenheit in allen historischen Batchläufen ist damit
nicht bewiesen. Eine streng unberührte Herkunft wird nicht behauptet.

GE0019 wurde als Ein-Rechteck-Komposition und DLG0071 als bekannte Panelvariante
ausgeschlossen. GE0018 enthält überlappende Rechtecke statt einem einzelnen
oder zwei getrennten Rechtecken. GE0307 enthält vier getrennte Felder statt
drei lückenlos anschließenden Flaggenstreifen. GE0309 und andere nordische
Flaggen zählen zur selben neuen Familie. Dies ist kein allgemeiner
Familienannotationsaudit. Beide geprüften Fälle sind künftig bekannte
Entwicklungsdaten; das historische Freeze behält den damaligen Prüfstatus.
Spätere Verbesserungen an ihnen sind keine neuen unabhängigen Familien.
Der Vierfelderfall benötigt einschließlich Kreis fünf Objekte und liegt damit
außerhalb der bisherigen Szenenanzahl. Die Versuche untersuchen neue
Zusammensetzungen bekannter Primitive; sie belegen keine Regression zuvor
unterstützter Szenenverträge und ersetzen keine erfolgreiche Übertragungsabnahme.

## Ursache und nächste Entwicklung

Die Codepfadprüfung ergibt: Der gemeinsame Szeneneinstieg erreicht den gemischten Verlaufsvertrag, der
beide vollständigen Beschreibungen ablehnt. Er unterstützt eine Verlaufsscheibe
mit einem bzw. zwei getrennten, nicht gerundeten Rechtecken. Überlappung,
Rundung in diesem gemischten Weg und vier Kinder fehlen. Einzelfähigkeiten
anderer Szenenmodule werden noch nicht gemeinsam zusammengesetzt.

Die CLI-Ergebniszeilen enthalten keine `primitive_scene_registration`; native
Instanz- und Auswahlbelege fehlen ausdrücklich. Der vorhandene Ersatzweg
erzeugt unpassende Modelle und nennt dennoch intern `contract_status=ok`.
Dieser Status darf nicht als vollständige semantische Abnahme zählen;
die unabhängigen Gates weisen beide Ausgaben zurück.

Nächster Entwicklungsschritt **GENERAL-SCENE-COMPOSITION-09**: vorhandene
Rechteck-/Rundungs-/Überdeckungsbausteine und mehr als zwei Kinder über einen
gemeinsamen Verlaufsszenenvertrag verbinden. Alle Beschreibungsaussagen müssen
verbraucht und Instanz-/Auswahlbelege ausgegeben werden. Synthetische Kontrollen
und die jetzt bekannten Fehlfälle dienen als Entwicklung. Zwei andere reale
Familien vor Entwicklung markieren und sperren; keine Nachstimmung auf deren
Ergebnisse. Keine Symbolvorlagen, Katalogkennungen oder schwächeren Gates.

## Nachweise und Reproduktion

`artifacts/evaluation/real_scene_transfer_v1/` enthält Original-JPEGs,
fixierte CLI-Eingaben, Markierungen, Runtime-Hashes, tatsächliche SVGs,
Vergleichsbilder, vollständige Ergebniszeilen, Worker-/Aufsichtslogs,
Zugriffsbelege und negative Entscheidungen. `manifest.json` inventarisiert
sämtliche Dateien mit Prüfsummen.

Vergleichsbilder, jeweils links Original, mittig Ausgabe und rechts Differenz:
[Kreuz](../artifacts/evaluation/real_scene_transfer_v1/trial/real_00/comparison.png),
[Vierfelderflagge](../artifacts/evaluation/real_scene_transfer_v1/trial/real_01/comparison.png).

Der neue Prüfer rendert gespeicherte SVGs und prüft Originalpixel, Objekt-/
Regionsgates, Runtime-Freeze, Budget, Zugriffssperren und Vollständigkeit erneut.
Er startet keinen Converter und verändert keine Belege. Exit 0 bestätigt
konsistente Evidenz; `--require-all` verlangt positive Abnahme und endet hier
erwartungsgemäß mit 1. Neun gezielte Tests prüfen auch verfälschte Entscheidungen,
fehlende Versuche, geänderte Markierungen, Runtime, Seeds, Budgets und Zugriffe.
Die gemeinsame Szenenprüfung erhält dafür einen optionalen schreibfreien Modus.

```powershell
.venv/Scripts/python.exe -m tools.verify_real_scene_transfer_evidence artifacts/evaluation/real_scene_transfer_v1/manifest.json --output .tmp/transfer-verified.json
.venv/Scripts/python.exe -m tools.verify_real_scene_transfer_evidence artifacts/evaluation/real_scene_transfer_v1/manifest.json --output .tmp/transfer-acceptance.json --require-all
.venv/Scripts/python.exe -m pytest tests/test_real_scene_transfer_evidence.py -q

# Neue Ordner verwenden; Wiederholungen sind keine neue Familienabnahme.
.venv/Scripts/python.exe -m tools.evaluate_real_scene --prepare .tmp/transfer-input-new --real --annotations config/real_scene_transfer_families.json
.venv/Scripts/python.exe -m tools.evaluate_real_scene --inputs .tmp/transfer-input-new --output .tmp/transfer-cli-new
```

Alle Produktionsdateien unter `src/` sind hashgleich zum Freeze. Alle 758
Bild-/SVG-Prüfsummen stimmen mit dem Archivindex überein: **379 Paare**, kein
Kataloggewinn. Eine erneute vollständige Archivkonvertierung erfolgte für diese
Untersuchung ohne Runtime-Änderung nicht.
