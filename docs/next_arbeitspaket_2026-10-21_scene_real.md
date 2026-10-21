# Reale Szenenprüfung und typisierte Farb-/Lagebezüge

Arbeitspaket: **GENERAL-SCENE-REAL-05**.
Branch: `codex/general-scene-real-05-2026-10-21`.
Ausgangsstand: `2dcd915bf` auf `main`.

## Ergebnis und Geltungsbereich

Der begrenzte Szenenweg kann eindeutige Farb- und Lagebezüge zusätzlich zu
Größenrollen auswerten. Er verlangt weiterhin zwei bis drei einfarbig gefüllte
Kreise/achsparallele Rechtecke mit beobachtbarer partieller Überdeckung,
optional eigenen dunklen Konturen und expliziter Verschachtelung.
Unbekannte Beziehungen und mehrdeutige Referenzen werden zurückgewiesen.

Die vier vor Entwicklung visuell markierten realen Familien bestehen weder
vorher noch nachher die vollständige unabhängige Abnahme (**0/4 → 0/4**).
Das ist ein negatives reales Ergebnis: Die markierten Originale enthalten
zusätzlich offene Konturen, Schrift, Verläufe, gerundete Ecken oder komplexe
Innenformen. Die erfolgreichen Sprachprüfungen sind synthetische Kontrollen
und belegen keinen Erfolg bei diesen realen Zusatzinhalten.

Das Nullergebnis gilt für die hier verwendeten eigenständigen Beschreibungen
und das Fünf-Sekunden-Budget. Der Versuch isoliert den Einfluss anderer
Formulierungen nicht von fehlenden Inhaltsmodellen. Insbesondere besitzt die
bekannte Spiralfamilie bereits einen separaten Spezialweg für dessen engere
Beschreibung; ihre Verwendung hier belegt keine generelle Unfähigkeit des
Converters, Spiralscheiben zu rekonstruieren.

Die nachgewiesene Katalogzahl bleibt **377/1.785 (21,1 %)**: 329 reguläre
`semantic-only`- und 48 historische `standard`-Archivpaare. Es gibt keine
neue reale Katalogabnahme. Die Qualitätsgrenzen wurden nicht verändert;
das optionale neuronale Netz bleibt ausgeschaltet.

## Vorab markierte und gesperrte reale Familien

`config/real_scene_families.json` hält Originalprüfsummen, vorhandene
Katalogbeschreibungen, eigenständige Bildbeschreibungen, manuell markierte
sichtbare Grenzen und unbekannte Zusatzinhalte fest. Die Markierung entstand
an den Originalrastern und mit nächster-Nachbar-Vergrößerung, vor Änderung
der Runtime. Weder Detektorvorschläge noch erzeugte oder vorhandene SVGs
lieferten die Markierung. Die Boxen sind sichtbare Näherungen; verdeckte
Geometrie wird daraus nicht behauptet.

| Familie | Partition | Beobachtung und Grenze |
| --- | --- | --- |
| `AC0160.JPG` | Entwicklung | Rechteckanzeige vor offenem Doppelrahmen; Schrift und offene Hintergrundseiten |
| `DLG0011.JPG` | Entwicklung | Verschachtelte helle Rechteckfläche; gerundete Außenkontur und Verlauf |
| `AC0422_L.jpg` | bekannte Entwicklungskontrolle | Kreisscheibe mit Spirale und schrägen Innenlinien |
| `GE0360.jpg` | gesperrte Prüfung | Überlagerte Embleme auf Verlaufsscheibe; Werkzeuge und Schneeflocke |

Alle Größen-, Farb- und Orientierungsnachkommen einer Topologie gehören zur
selben Partition. Ein abschließender Familienaudit fand die Spiraltopologie
bereits als `AC0424_1_L` im früheren Netzversuch. Ihre ursprüngliche Einordnung
als unbekannter Holdout war falsch: Sie zählt ausschließlich als bekannte
Entwicklungskontrolle. Der Audit und die ursprüngliche Annotation-Prüfsumme
stehen in `selection_audit` im Konfigurationsmanifest. Die übrigen drei
Topologien sind neue Szenenfamilien; das verschachtelte Panel ergänzt eine
innere weiße Fläche gegenüber dem früheren einzelnen Panel. Die neue
gesperrte reale Prüffamilie ist `GE0360`; sie wurde nicht zur Algorithmus-
oder Grenzenauswahl verwendet. Alle Annotationen und Raster
waren vor der Entwicklung festgelegt; die Vorher-CLI lief ebenfalls vorher.
Nach diesem Versuch sind alle vier Familien Entwicklungsdaten. Eine neue
reale Abnahme benötigt neue gesperrte Familien.

Die CLI erhält eine verlustfreie PNG-Kopie der dekodierten Original-JPEG-Pixel
und die eigenständige Beschreibung. Die Original-JPEG-Prüfsumme bleibt im
Manifest. Dateinamen werden neutralisiert. Die Katalogdateien werden nicht
umgeschrieben. Unbekannter Inhalt bleibt im Objektnachweis erhalten und darf
nicht durch ein erfolgreiches Teilobjekt ersetzt werden.
Ein `unknown` ist ein Platzhalter für zusätzlichen nicht modellierten Inhalt,
kein vollständiger Instanz-/Tiefengraph dieses Inhalts. Die native Objektprüfung
kann solche Szenen nicht freigeben. Alle vier realen Ausgaben scheitern
zusätzlich bereits an der unabhängigen globalen Pixelprüfung; ihr Nullergebnis
entsteht somit nicht nur durch den unbekannten Objekttyp im Manifest.

## Umsetzung

`imageCompositeConverterSceneReferences.py` übersetzt die begrenzte Grammatik
in typisierte Referenzen und Relationen. Unterstützte Rollen sind Größen,
linke/rechte/obere/untere Form sowie rote, orange, gelbe, grüne, blaue,
violette, graue, schwarze und weiße Form. Farbrollen beziehen sich auf die
beobachtete Füllung, nicht auf die Kontur. Die Farbauswertung verwendet breite
HSV-Innenbereiche mit Unsicherheitslücken. Nicht modellierte Farbbereiche
werden nicht zur nächstliegenden Farbe umgedeutet.

Beispiele:

- „Die orange Form liegt vor der blauen Form.“
- „Die linke Form liegt hinter der rechten Form.“
- „Die grüne Form liegt innerhalb der blauen Form.“
- „Die blaue Form liegt oberhalb der orangen Form.“

Jede angeforderte Farbrolle muss genau eine Instanz identifizieren.
Lagerollen verlangen einen eindeutigen Extremwert der Objektmitten mit
mehr als drei Pixeln Abstand zum nächsten Kandidaten. Sie bedeuten keine
vollständige Trennung der Außenkanten. Größenrollen behalten ihren
bisherigen Abstandsfaktor 1,12; reine Farbrollen erfordern keine verschiedenen
Objektgrößen. Verschiedene Namen für dieselbe Instanz erzeugen keinen
zulässigen Selbstbezug.

`vor`/`hinter` binden die Zeichenreihenfolge, `innerhalb` zusätzlich die echte
native Verschachtelung. `links von`/`rechts von`/`oberhalb`/`unterhalb` binden
die relative Lage der Mitten. Geometrie und aktuelle Füllparameter werden bei
jedem Verfeinerungsschritt erneut geprüft. Die bestehende beobachtete
gemeinsame Innenfläche muss die Zeichenreihenfolge weiter stützen; ein guter
globaler Pixelwert überstimmt diese Bedingung nicht.

Unverbrauchte Objektbezugssätze, unbekannte Prädikate, Negationen, doppelte
Farben, ausgerichtete Lagekandidaten und widersprüchliche Aliase scheitern
konservativ. Der Dispatcher lässt solche Sätze bei partieller Überdeckung
nicht in die ältere, weniger strenge Fusion ausweichen. Die bestehende
Aussage „Eine Form liegt getrennt“ behält ihren bisherigen Fusionsweg.
Begrenzte Formulierungen über Skalierung/Verschiebung des gesamten Motivs
werden gesondert erkannt; die tatsächlichen Maße kommen weiter aus dem Bild.

## Unabhängige Nachweise

`tools.evaluate_real_scene` nutzt den bestehenden echten CLI-Runner mit
isoliertem Fünf-Sekunden-Bildbudget, Suchseed 17, 64 angeforderten Iterationen
und äußerer Prozessgrenze 30 Sekunden. Referenz-SVG-Lesezugriffe sind im
Worker gesperrt. Jede gespeicherte Ausgabe wird unabhängig erneut gerendert.
Native Formarten/-anzahl, Außenmaße (maximal 2,5 Pixel Abweichung),
Konturbreiten (maximal 0,85 Pixel), Zeichenreihenfolge, jede Objektregion und
die bestehenden globalen Pixel-/Komplexitätsgates bleiben verbindlich.

| Prüfgruppe | Ergebnis |
| --- | ---: |
| Vorab eingefrorene Sprachkontrollen, Seed 871209 | 0/12 → 12/12 |
| Erste zusätzliche Prüfszenen, Seed 139627 | 12/12 |
| Nach letztem Runtime-Freeze erzeugte, umformulierte Prüfszenen, Seed 523891 | 12/12 |
| Neutrale Umbenennungen beider zusätzlicher Prüfsätze | jeweils 12/12, SVGs bytegleich |
| Erweiterte Vorlage, Seed 416725, umformulierte Tiefenbezüge | 17/17 |
| Absichtlich widersprüchliche Tiefenbezüge, Seed 331967 | 0/6 akzeptiert |
| Lokaler CI-Sprach-Smoke, Seed 762915 | 6/6 |
| Unabhängig markierte Originalfamilien | 0/4 → 0/4 |

Der erste Variantenversuch bestand nur 1/17: Qualitative Richtungswörter in
der Ganzmotivverschiebung wurden als Objektbezug verworfen. Die vollständigen
fehlgeschlagenen Versuche bleiben unter `.tmp/real05/plan-b-cli` erhalten;
nach Korrektur bestand derselbe eingefrorene Satz 17/17. Außerdem deckte die
Szenenregression eine zu breite Auswahl des neuen Dispatchers auf; die
bisherigen Fusionsfälle behalten nach Korrektur ihren bisherigen Weg.

Die abschließenden Szenenregressionen bestehen mit **181/181 Tests**.
Alle **377/377 Archiv-Neukonvertierungen** bestehen die bestehende absolute
Archiv-Pixelgrenze. Alle **764 gespeicherten Archivdateien** bleiben
hashgleich. Bei 42 Neukonvertierungen liegt der Fehler über dem jeweils
gespeicherten historischen Bestwert; die absolute Abnahme behauptet keine
Gleichheit mit diesen Bestresultaten. Keine der 377 Archivbeschreibungen
aktiviert den neuen Sichtbarkeits-/Referenzweg. Der Archivlauf begann vor
der letzten rein sprachlichen Verfeinerung dieses für das Archiv inaktiven
Wegs. Der Verlauf der Batch-Messwerte ist damit kein Nachweis eines
Einflusses der neuen Referenzauflösung. Die gespeicherten besseren Ausgaben
bleiben erhalten. Einzelwerte stehen im vollständigen Archivbericht.
Gegenüber dem vorigen Sichtbarkeits-Archivlauf ändern sich fünf Werte:
`AC0414_L`, `AC0413_S` und `AC0424_M` nach unten, `AC0424_S` und `AC0910_M`
nach oben. Die Ursache dieser Batchabweichungen wurde nicht gesondert
nachgewiesen. Prüfsummen beider Berichte und die fünf Werte stehen in der
Zusammenfassung; die Kopie des Vorberichts liegt lokal unter
`.tmp/real05/previous-archive-report.json`.
Die vollständige normale Standardsuite besteht mit **3.722 bestandenen und
30 regulär übersprungenen Tests**. Alle **3.752 gesammelten Test-IDs** sind
im vollständigen XML-Bericht genau einmal enthalten; keine Fehler. Die drei
im Standardprofil ausgeschlossenen schweren Module wurden nicht zusätzlich
gestartet. Die beobachtete Laufzeit beträgt 19.222,30 Sekunden (5:20:22),
einschließlich sehr langer bestehender Windows-Konvertierungstests. Die Ursache
dieser Langläufe wurde in diesem Paket nicht untersucht; daraus wird kein
Performancevergleich des neuen Referenzwegs abgeleitet. Syntaxprüfung für
`src`, `tests` und `tools`, CLI-Help, Bild-ID-Hardcoding-Nullprüfung und
Whitespace-Prüfung unter Beachtung bestehender CRLF-Zeilenenden bestehen.

Der neue CI-Job `named-scene-references` prüft Sprachkontrollen und reale
Raster einschließlich erneuter unabhängiger Prüfung. Bei den realen Fällen
zeichnet er das Ergebnis auf, ohne vollständige Erfolge zu unterstellen.
Ein entfernter CI-Lauf wurde nicht ausgelöst.

## Reproduktion und Ablage

Alle folgenden Ausgabeverzeichnisse müssen neu sein:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_real_scene --prepare .tmp/real05/real-inputs --real
.venv/Scripts/python.exe -m tools.evaluate_real_scene --inputs .tmp/real05/real-inputs --output .tmp/real05/final-challenge
.venv/Scripts/python.exe -m tools.evaluate_real_scene --prepare .tmp/real05/dev-frozen-inputs --seed 871209 --count 12
.venv/Scripts/python.exe -m tools.evaluate_real_scene --inputs .tmp/real05/dev-frozen-inputs --output .tmp/real05/final-language --require-all
.venv/Scripts/python.exe -m tools.evaluate_real_scene --prepare .tmp/real05/holdout-inputs --seed 139627 --count 12
.venv/Scripts/python.exe -m tools.evaluate_real_scene --inputs .tmp/real05/holdout-inputs --output .tmp/real05/final-holdout --require-all
.venv/Scripts/python.exe -m tools.evaluate_real_scene --inputs .tmp/real05/holdout-inputs --output .tmp/real05/final-rename --rename --require-all
.venv/Scripts/python.exe -m tools.evaluate_real_scene --prepare .tmp/real05/sealed-final-inputs --seed 523891 --count 12 --paraphrase
.venv/Scripts/python.exe -m tools.evaluate_real_scene --inputs .tmp/real05/sealed-final-inputs --output .tmp/real05/final-sealed --require-all
.venv/Scripts/python.exe -m tools.evaluate_real_scene --inputs .tmp/real05/sealed-final-inputs --output .tmp/real05/final-sealed-rename --rename --require-all
.venv/Scripts/python.exe -m tools.evaluate_real_scene --prepare .tmp/real05/plan-b-inputs --seed 416725 --count 3 --variations --paraphrase
.venv/Scripts/python.exe -m tools.evaluate_real_scene --inputs .tmp/real05/plan-b-inputs --output .tmp/real05/final-plan-b --require-all
.venv/Scripts/python.exe -m tools.evaluate_real_scene --prepare .tmp/real05/negative-inputs --seed 331967 --count 6 --contradict
.venv/Scripts/python.exe -m tools.evaluate_real_scene --inputs .tmp/real05/negative-inputs --output .tmp/real05/final-negative
.venv/Scripts/python.exe -m tools.evaluate_real_scene --prepare .tmp/real05/ci-inputs --seed 762915 --count 6 --paraphrase
.venv/Scripts/python.exe -m tools.evaluate_real_scene --inputs .tmp/real05/ci-inputs --output .tmp/real05/final-ci --require-all
.venv/Scripts/python.exe -m pytest -q tests/test_scene_references.py tests/test_scene_visibility.py tests/test_scene_fusion.py tests/test_layered_scene_runtime.py tests/test_primitive_scene_runtime.py --basetemp=.tmp/real05/pytest-accepted-scenes --junitxml=.tmp/real05/scene-accepted.xml
.venv/Scripts/python.exe -m pytest -q --durations=10 --basetemp=.tmp/real05/pytest-reconnected-standard --junitxml=.tmp/real05/standard.xml
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --output-dir .tmp/real05/archive-recheck --max-cases-per-worker 60
```

Die kompakte Zusammenfassung unter `artifacts/evaluation/real_scene_v1/`
enthält Prüfzahlen und Prüfsummen. `tools.summarize_real_scene_evaluation`
rendert alle vollständigen lokalen Ergebnisse erneut, kontrolliert die
Runtime-Prüfsummen, Bytegleichheit der Umbenennungen, eingefrorene Annotationen,
Tests und Archivdateien. `--verify-only` vergleicht zusätzlich die gespeicherte
Zusammenfassung. Vollständige Raster, SVGs und Workerberichte bleiben lokal
unter `.tmp/real05/`; CI lädt seinen eigenen vollständigen Lauf hoch.
Die Zusammenfassung allein ersetzt keine neue unabhängige Prüfung.

Die historischen Vorher-Läufe und der fehlerhafte erste Variantenlauf lassen
sich nur mit ihren jeweiligen damaligen Runtime-Ständen reproduzieren. Ein
frischer Checkout besitzt diese Rohdaten nicht. Das Zusammenfassungswerkzeug
prüft sie, wenn sie vollständig vorhanden sind; der normale CI-Nachweis und
die obigen finalen Einzelprüfungen benötigen sie nicht.

## Folgearbeit

**GENERAL-SCENE-REAL-06** soll zuerst die reale verschachtelte Paneltopologie
mit Verlauf und gerundeter Kontur bearbeiten, mit getrenntem Nachweis für
Füllung, Kontur und innerer heller Fläche. Die vier jetzt untersuchten
Familien sind nur noch Entwicklung; neue reale Prüf- und Negativfamilien
müssen vor weiterer Runtime-Entwicklung markiert und gesperrt werden.
Spiralen, offene Rahmen/Schrift und zusammengesetzte Embleme benötigen eigene
Inhaltsmodelle. Ein ausreichend guter Gesamtpixelwert genügt dafür nicht.
Produktive Netzabnahme, IDO-19/IDO-21 und SEARCH-DEADLINE-COMPAT behalten
ihren bisherigen Status.
