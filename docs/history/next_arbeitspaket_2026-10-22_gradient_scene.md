# Rechteckszenen mit Verlauf und gerundeten Ecken

Begrenztes Entwicklungspaket **GENERAL-SCENE-GRADIENT-06**, als konkreter
Folgeschritt von GENERAL-SCENE-REAL-05. Branch:
`codex/general-scene-real-05-2026-10-22`; Ausgangsstand `631b058016`.

## Ergebnis und verbleibende Abnahme

Der gemeinsame Einstieg für native Szenen registriert jetzt ein bis drei
getrennte Rechtecke mit horizontalem oder vertikalem Zweipunktverlauf sowie
zwei verschachtelte Rechtecke mit weißer Innenfläche. Gerundete Ecken und
explizite dunkle Konturen sind eigene Parameter. Geometrie und Farben kommen
aus Raster und Beschreibung; es gibt keine Familienkennung, gespeicherte
Symbolvorlage oder als Ausgabe übernommene Rasterkontur.

Die bekannten verschachtelten Originale `DLG0011` und `DLG0018` verbessern sich
bei denselben eigenständigen Beschreibungen von **0/2 auf 2/2**. Beide bestehen
die beiden unveränderten regulären Gates, die strengeren globalen Pixelgates
und native Objekt-/Regionsprüfungen ohne Pflichtmetrikregression. Die beiden
Kataloge enthalten jetzt diese eigenständigen Beschreibungen. Die tatsächlich
geprüften Originale und Vorher-/Nachher-SVGs bleiben im Belegordner erhalten.
Das Erfolgsarchiv wächst von 377 auf 379 Paare (21,2 % von 1.785 Bildern).
Alle 377 bisherigen Datensätze sowie deren 754 Bild-/SVG-Dateien bleiben
unverändert; die neue Gesamtzahl ist kein neuer Familienzähler.
Die 377 alten und zwei neuen Archivfälle wurden getrennt erneut konvertiert
und bestehen die unveränderte absolute Archivgrenze. Die zwei neuen
JPEG-Konvertierungen sind bytegleich zu den gespeicherten SVGs und bestehen
zusätzlich die strengeren Objekt-/Pixelprüfungen. Bei 41 alten
Neukonvertierungen liegt der Fehler über dem gespeicherten Bestwert;
deren bessere Archiv-SVGs bleiben erhalten. Keine der 377 bisherigen
Archivbeschreibungen aktiviert den neuen Gradientenweg. Diese absolute
Bestandsprüfung behauptet keine Gleichheit aller frisch erzeugten Alt-SVGs
mit ihren historischen Bestresultaten.

Das sind **zwei Varianten einer bereits bekannten Topologie**, keine zwei
neuen realen Familien. Alle vier Originalfälle sind ausdrücklich Entwicklung;
es gibt keine neue gesperrte reale Familienabnahme. GENERAL-SCENE-REAL-05
bleibt offen, insbesondere sein Nachweis an mindestens zwei neuen realen
Familien. Dieses Paket schließt den begrenzten Implementierungsschritt ab.

Die einflächigen Originale `DLG0012` und `DLG0017` bestehen die unabhängige
Vordergrund-IoU-Prüfung weiterhin nicht. Ihr Verlauf berührt fast den gesamten
Bildrand; die unabhängige Hintergrundschätzung und die lokale weiße
Hintergrundmaske des Registrierers bewerten diesen Fall unterschiedlich.
Ein geringer Gesamtpixelfehler hebt diese Ablehnung nicht auf. Ihre
Katalogbeschreibungen und die Qualitätsgrenzen wurden nicht geändert.

## Modell und Begrenzung

Der Szeneneinstieg verwendet weiterhin die überwachte Produktions-CLI mit
fünf Sekunden Bildbudget, Seed 17 und 64 angeforderten Iterationen. Komponenten
des Vordergrunds liefern alternative Rechteckgrenzen; eingeschlossene helle
Löcher liefern die weiße Innenfläche. Der Eckenradius wird aus der fehlenden
Konturfläche initialisiert. Eine robuste affine Farbregression auf sichtbaren
Innenpixeln liefert die Verlaufendpunkte, auch bei dünnen sichtbaren Rändern.
Der reguläre Registrierer verfeinert Seiten, Radius, Kontur und Farben gemeinsam.
Ein grober Pixelpass beendet die Suche erst bei hinreichend kleinem mittlerem
Farbfehler früh, damit Subpixelverschiebungen und Radien weiter verfeinert werden.
Diese Suchbedingung ersetzt keine der unveränderten Abnahmegrenzen.

Ausgegeben werden native `rect`-Elemente und `linearGradient`-Definitionen mit
zwei Farbstopps. Objektanzahl, Trennung auf der beschriebenen Achse,
Verschachtelung, weiße Innenfüllung und Verlaufsrichtung bleiben verbindlich.
Flache Füllungen und sichtbar inkompatible Verlaufsrichtungen können die
Gradientenregistrierung nicht allein über einen großzügigen globalen Pixelwert
bestehen. Wegen JPEG-Rauschen gibt es eine begrenzte Unsicherheit der
Farbregression; eine beliebig schwache oder beliebig verlaufende Füllung wird
nicht behauptet.

Die Grammatik ist absichtlich klein: zum Beispiel
„Zwei gefüllte Rechtecke mit leicht gerundeten Ecken. Die Formen sind ineinander
verschachtelt. Die äußere Form hat einen horizontalen Farbverlauf. Die innere
Form ist weiß. Keine Beschriftung.“ Unverbrauchte Inhalts-, Negations- und
Beziehungsaussagen verwerfen diesen Modellweg. Er ist kein allgemeiner
Sprachparser. Teilüberdeckungen, farbige Kinder, komplexere Verläufe und
Mischungen mit anderen Formarten gehören nicht zu diesem Umfang.

## Unabhängige Prüfungen und Fehlversuche

Die Auswertung rendert gespeicherte SVGs erneut und prüft Anzahl, Formart,
Außenmaße, Zeichenreihenfolge, Konturbreite und Eckenradius. Neue synthetische
Referenzen binden zusätzlich die native Verlaufsachse und weiße Innenfüllung.
Der externe Konvertierungsworker darf Referenz-SVGs nicht lesen. Er erhält
neutrale Dateinamen, Raster und Beschreibung; die Geometrieorakel bleiben
außerhalb des Workers.

- Zwölf Entwicklungsfälle bestehen 12/12.
- Zwölf neue, nach letztem Runtime-Freeze erzeugte und umformulierte Fälle
  bestehen 12/12; ihre zwölf Umbenennungen ebenfalls, mit bytegleichen SVGs.
- Die abschließende unabhängige Plan-B-Vorlage besteht Original plus 16
  Varianten, also 17/17, einschließlich der Radius- und Konturprüfungen.
- Die gezielte Szenenregression besteht mit 217/217 Tests. Fünf zusätzliche
  Tests prüfen die gespeicherten realen Gate-Belege und manipulierte Hashes.
- Drei gezielte widersprüchliche CLI-Beschreibungen erreichen 0/3 unabhängige
  Freigaben. Das ist eine fachliche Ablehnung; ein CLI-Exitcode allein gilt
  weiterhin nicht als Qualitätsurteil.

Der erste Variantenlauf bestand nur **8/17**: Python-`casefold` wandelt das ß
in „größer“ in `ss` um; die Grammatik hatte anschließend noch nach ß gesucht.
Nach dieser Korrektur bestanden **14/17**; drei Fälle scheiterten an der
unabhängigen Radiusprüfung trotz bestandenem Pixelgate. Eine genauere
Verfeinerung vor frühem Sucherfolg brachte denselben Satz auf **17/17**.
Alle Fehlversuche bleiben im lokalen Belegbestand und in der Zusammenfassung.

Ein erster zusätzlich isolierter Elternsnapshot ohne vollständigen Projektbaum
lieferte keine vollständige Prüfmatrix und zählt nicht als Qualitätsvergleich.
Der verwendete Vorher-Nachweis ist der zuvor vollständig geprüfte Lauf im
unveränderten Hauptcheckout. Bei einem der beiden zusätzlichen Einzelpanels
enthielt die erste Beschreibung einen Schreibfehler (`verticalem`); die
korrigierte Fassung lautet `vertikalem`. Die kausale 0/2→2/2-Aussage betrifft
ausschließlich die beiden unverändert beschriebenen verschachtelten Originale.

## Reproduktion und Ablage

Neue Ausgabeverzeichnisse verwenden:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_gradient_scene --prepare .tmp/gradient-real --real
.venv/Scripts/python.exe -m tools.evaluate_gradient_scene --inputs .tmp/gradient-real --output .tmp/gradient-real-cli
.venv/Scripts/python.exe -m tools.evaluate_gradient_scene --prepare .tmp/gradient-holdout --seed 923087 --count 12 --paraphrase
.venv/Scripts/python.exe -m tools.evaluate_gradient_scene --inputs .tmp/gradient-holdout --output .tmp/gradient-holdout-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_gradient_scene --inputs .tmp/gradient-holdout --output .tmp/gradient-holdout-renamed --rename --require-all
.venv/Scripts/python.exe -m tools.evaluate_gradient_scene --prepare .tmp/gradient-variants --seed 837645 --variations --paraphrase
.venv/Scripts/python.exe -m tools.evaluate_gradient_scene --inputs .tmp/gradient-variants --output .tmp/gradient-variants-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_gradient_scene_acceptance artifacts/evaluation/gradient_scene_v1/manifest.json --output .tmp/gradient-acceptance.json
.venv/Scripts/python.exe -m pytest tests/test_gradient_scene_runtime.py tests/test_gradient_scene_acceptance.py tests/test_layered_scene_runtime.py tests/test_scene_references.py tests/test_scene_visibility.py tests/test_scene_fusion.py tests/test_primitive_scene_runtime.py -q
```

`config/gradient_scene_families.json` enthält die bekannten Originale und
Prüfsummen. `artifacts/evaluation/gradient_scene_v1/` enthält die zwei
unveränderten Original-JPEGs, gespeicherte CLI-SVGs, den reproduzierbaren
regulären Gate-Bericht und kompakte Zusammenfassungen. Vollständige lokale
Versuche stehen unter `.tmp/real06/`. Historische Vorher-Versuche benötigen
ihren damaligen Code; sie sind keine auf einem frischen Checkout erneut
behauptete Messung. `tools.summarize_gradient_scene_evaluation` prüft die
vollständigen lokalen Ausgaben und bindet finale Gruppen an aktuelle
Runtime-Prüfsummen. Der neue CI-Job `rounded-gradient-scenes` erzeugt eigene
Belege und lädt sie hoch; ein entfernter Lauf wurde nicht ausgelöst.

Standardtest-, Archiv- und Hashnachweise stehen in `checks.json` im
Belegordner. Sie unterscheiden erhaltenen Altbestand und neue Varianten.
Die finale eindeutige Standardabdeckung umfasst **3.838 Test-IDs**:
**3.808 bestanden, 30 regulär übersprungen, null Fehler**. Im ersten
vollständigen Modulbestand scheiterte ein bestehender Zeittest:
`sleep(50 ms)` ergab 47 ms Differenz auf Windows' monotoner Uhr
`GetTickCount64` mit 15,625 ms Auflösung. Der Test der gespeicherten Zeitlücke
verwendet jetzt eine kontrollierte Uhr; produktiver Zeitcode und Limits
bleiben unverändert. Seine neun Modultests bestehen erneut. Die finale
Abdeckung ersetzt nur dieses Modul durch den Wiederholungslauf; der
ursprüngliche Fehlversuch bleibt einschließlich XML-Prüfsumme dokumentiert.
Syntaxprüfung, CLI-Hilfe, Bild-ID-Hardcoding-Nullprüfung und die
Whitespace-Prüfung unter Beachtung der bestehenden CRLF-Zeilenenden bestehen.
Die Standardsuite wird modulweise in frischen Prozessen geprüft. Der erste
gemeinsame Prozess wurde nach langen bestehenden Konvertierungstests bei
ungefähr 54 % beendet und zählt nicht als abgeschlossener Lauf. Der finale
Nachweis gleicht sämtliche Modul-XMLs mit einer frischen vollständigen
Sammlung der Test-IDs ab. Bis zu sechs Modulprozesse laufen gleichzeitig;
OpenCV verwendet darin einen Thread. Die drei regulär ausgeschlossenen
schweren Testmodule bleiben separat. Die Befehle für eine serielle
Wiederholung aller in `checks.json` aufgeführten Module sind:

```powershell
$checks = Get-Content artifacts/evaluation/gradient_scene_v1/checks.json -Raw | ConvertFrom-Json
foreach ($module in $checks.standard_suite.modules) {
    .venv/Scripts/python.exe -c 'import cv2,pytest,sys; cv2.setNumThreads(1); sys.exit(pytest.main(sys.argv[1:]))' -q $module.path
    if ($LASTEXITCODE -ne 0) { throw "Testmodul fehlgeschlagen: $($module.path)" }
}
```

## Weiterhin offen

Unbekannte reale Familien vor weiteren Runtime-Änderungen markieren und
sperren. Mindestens zwei neue Kombinationen bereits unterstützter Primitive
über denselben Szenenweg nachweisen; Farb-, Größen- und Orientierungsvarianten
weiterhin getrennt zählen. Die zwei einflächigen IoU-Fehler bleiben ebenfalls
sichtbar. GENERAL-SCENE-REAL-05, der praktische Nutzenvergleich und die
historische Kompatibilitätsaufsicht behalten ihren offenen Status.
