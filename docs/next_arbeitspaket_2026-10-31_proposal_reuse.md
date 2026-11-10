# P0: Identische native Strukturvorschläge einmal vermessen

Begrenzter Teil von **SEARCH-STRUCTURE-01**, Rang 1 der
[Prioritätenliste](task_priority_2026-10-24.md). Ausgangscommit `8cca41953`.
Die bereits dokumentierte Anforderung, doppelte Vorschläge unter demselben
Bildbudget zu vermeiden, gilt jetzt auch für ihre native Vermessung.

## Ursache und Umsetzung

Die Schwellwerte 25, 16 und 36 können unterschiedliche Restbildmasken, aber
dieselben beobachteten Füllgruppen liefern. Bisher wurden deren Kreisradien,
Konturen und Rechteckrundungen dreimal vermessen, bevor der gemeinsame
Strukturvergleich den doppelten Vorschlag erkannte. Im untersuchten
Vier-Gruppen-Fall rief das Profil die Kreisvermessung 36-mal auf.

Ein auf genau einen Bild-/Suchaufruf begrenzter Speicher verwendet jetzt das
exakte Verlaufsfeld, die geordneten Farb-/Pixelgruppen und die Anforderungen
an Kreisformen, Rundung und Kontur als Schlüssel. Er enthält höchstens 96
Vorschläge einschließlich negativer Konturbelege. Die drei Zerlegungen sowie
Split- und Inselgruppenhypothesen teilen ihn. Änderungen der Beobachtung
führen zu einer neuen Vermessung; bearbeitbare Rückgaben sind tiefe Kopien.
Die unabhängige 96-Zustände-Grenze der Strukturagenda bleibt erhalten.

Nur die native Vorschlagserzeugung wird wiederverwendet. Objektinventar,
Gruppenzahl, Zeichenreihenfolge, vollständiger Beschreibungsvertrag,
Registrierung und lokale/globale Rastergates werden weiterhin geprüft.
`native_proposal`-Suchereignisse unterscheiden `measured` und `cache_hit` und
zählen beide. Ein erschöpftes Bildbudget startet weiterhin keine Registrierung.

## Gepaarter CLI-Vergleich

Vor der Runtimeänderung wurden zwölf unveränderte synthetische Szenen mit
Seed `731429`, vier getrennten Gruppen, Rundung und hellen Konturen gesichert
und über die echte CLI ausgeführt. Der Nachherlauf nutzt dieselben Rasterbytes,
Beschreibungen und unabhängigen Objektmarkierungen.

| Messung | Vorher | Nachher |
| --- | ---: | ---: |
| Unabhängig abgenommene CLI-Ausgaben | 12/12 | 12/12 |
| Bytegleiche SVGs zum Ausgangslauf | – | 12/12 |
| Native Gruppenvermessungen je Bild | 3 | 1 plus 2 Wiederverwendungen |
| Mediane überwachte Prozesszeit | 2,6015 s | 1,8360 s |
| Mediane Zeit des gesamten Prüflaufs je Fall | 3,7575 s | 3,0310 s |

Die überwachte Zeit enthält den isolierten Konvertierungsprozess; die äußere
Fallzeit enthält zusätzlich Prozessstart und erste Nachprüfungen. Das sind
verschiedene Messgrößen. Die lokale mediane Verbesserung beträgt rund 29 bzw.
19 Prozent und ist keine plattformübergreifende Laufzeitgarantie. Das feste
Bildbudget bleibt fünf Sekunden, der äußere Notabbruch 30 Sekunden.

Die drei im vorherigen Paket dokumentierten Vier-Gruppen-Zeitlimitfehler
wurden heute **nicht reproduziert**: Bereits der unveränderte Ausgangsstand
besteht alle 18 ausgewählten Gruppenregressionen und die zwölf CLI-Fälle.
Dieses Paket beansprucht deshalb keine Reparatur jener historischen Fehler.

Kompakte Eingabe-/Ausgabe-/Runtimehashes, Messwerte, native Prüfergebnisse und
Suchereignisse stehen in
[`overlap_proposal_reuse_v1`](../artifacts/evaluation/overlap_proposal_reuse_v1/README.md).
Rohdaten bleiben gemäß Repositoryregel unter `.tmp/composition-transfer/`.

## Abnahmegrenzen

Der betroffene Regressionsblock besteht **599/599 Tests**, Exit 0, ohne
Überspringung. Die **elf neuen Prüfungen sind darin enthalten**, keine
zusätzlichen Versuche. Sie prüfen identische Vermessungen, veränderte
Füllgruppen und Reihenfolgen, geänderte Verlaufsfelder und Formanforderungen,
unverfälschte Rückgaben, negative Vorschläge, Bildtrennung und Speichergrenze.
Die bestehenden Szenenprüfungen behalten Objekt-, Relations-, Kontur-,
Raster-, Deadline- und Strukturzustands-Gegenproben.

Genau eine gekoppelte Plan-B-Kohorte mit Seed `853197`, zwei Gruppen,
Rundung, Konturen und 16 Transformationen besteht **17/17**, Exit 0. Ihr
Runtimehash stimmt mit dem gepaarten Nachherlauf überein. Das Kernprofil
besteht **42/42**, Exit 0. Syntax- und Diffprüfung bestehen ebenfalls.
Die Prüfbefehle, Exitcodes und JUnit-/Berichtshashes stehen in `checks.json`
im Evidenzordner. Eine zunächst wirkungslose Änderung einer Testpixelgruppe
wurde in den Testdaten korrigiert; dafür wurde keine Runtimegrenze geändert.

Dies ist eine Optimierung des bestehenden P0-Suchwegs, keine zusätzliche
Formfamilie oder neue reale Übertragungsabnahme. Die Quellenprüfung fand für
die zunächst erwogenen Panelbeispiele bereits gezielte historische Nutzung;
daraus wurde keine neue unabhängige Familie gemacht. Vor weiterer realer
Kompositionsentwicklung bleiben zwei andere Familien zu markieren und zu
sperren. **SEARCH-STRUCTURE-01**, **GENERAL-SCENE-COMPOSITION-09** und
**GENERAL-SCENE-REAL-05** bleiben offen. Archivpaare wurden nicht verändert.

Die vollständige Standardsuite und eine Archiv-Neukonvertierung gehören
nicht zur Abnahme dieses begrenzten Pakets. Die verwendete lokale Umgebung
ist Python 3.10.11; die historische Vorgabe 3.10.20 wird damit nicht belegt.

## Reproduktion

Neue Zielordner verwenden. Für einen erneuten Vorhervergleich dieselben
Eingaben im Ausgangscheckout `8cca41953` benutzen.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --prepare .tmp/reuse-inputs --seed 731429 --groups 4 --rounded --outlines
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --inputs .tmp/reuse-inputs --output .tmp/reuse-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --inputs .tmp/reuse-inputs --output .tmp/reuse-cli --verify-only --require-all
.venv/Scripts/python.exe -m pytest tests/test_overlap_proposal_reuse.py tests/test_overlap_groups.py -q
```

Der bestehende CI-Job `disconnected-overlap-groups` führt die neuen
Wiederverwendungsprüfungen zusammen mit den Gruppenregressionen aus.

## Sitzungslog / Status: Review

- Getestet: zwölf gepaarte echte CLI-Fälle, eine 17er-Variantenkohorte, 599 Regressionen und Kernprofil.
- Ergebnis: 12/12 vor/nach mit bytegleichen SVGs; Varianten 17/17, Regression 599/599, Kernprofil 42/42; lokale mediane überwachte Zeit rund 29 Prozent geringer.
- Grenzen: historische Zeitlimitfehler heute nicht reproduziert; neue reale Familienabnahme und allgemeine Komposition bleiben offen.
- Nächster Schritt: zwei andere reale Familien vor weiterer Kompositionsentwicklung markieren und sperren; SEARCH-STRUCTURE-01 fortsetzen.
- Startbefehl: `.venv/Scripts/python.exe -m pytest tests/test_overlap_proposal_reuse.py tests/test_overlap_groups.py -q`.
