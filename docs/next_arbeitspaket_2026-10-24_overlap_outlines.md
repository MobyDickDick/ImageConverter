# SEARCH-STRUCTURE-01: Konturen mit Überdeckung verbinden

Ausgangsstand `4c1e52ba2`, Branch
`codex/search-structure-overlap-outlines-2026-10-24`.
Die [verbindliche Rangfolge](weakness_review_2026-10-23.md) setzt
SEARCH-STRUCTURE-01 auf P0. Nach Rundung plus Überdeckung schließt dieses
Teilpaket die nächste ausdrücklich offene Kombination an: helle Konturen
bei zwei teilweise überlappenden Rechteckkindern im Verlaufskreis.

## Abgeschlossener Teilumfang und Grenzen

Der gemeinsame Szenenweg rekonstruiert native Rechtecke mit eigenen hellen
Konturen, wahlweise mit gerundeten Ecken. Verlauf, Instanzanzahl, Containment,
Zeichenreihenfolge, Radien und Konturbreiten bleiben gemeinsam prüfbar.
Beide Verlaufsachsen, beide Zeichenreihenfolgen und gespiegelte Anordnungen
sind synthetisch geprüft. Es entsteht keine neue Symbolvorlage.

Beispiel des vollständig konsumierten Beschreibungsvertrags:

> Ein gefüllter Kreis und zwei gefüllte Rechtecke mit leicht gerundeten Ecken.
> Der Kreis hat einen horizontalen Farbverlauf. Die Rechtecke liegen innerhalb
> des Kreises und überlappen sich teilweise. Keine Beschriftung.
> Die Formen haben helle Konturen.

Jede der vier Rechteckseiten benötigt mindestens fünf beobachtete Pixel.
Eine Kontur wird aus jeder freiliegenden Seite gemessen; inkonsistente,
fehlende und dunkle Konturen werden verworfen. Die neue Detektion ist auf
zwei unterscheidbare dunklere Füllfarben (mittlerer Kanalwert unter 180)
mit hellen, farblich identifizierbaren Konturen begrenzt. Kollineare
Eltern-/Füll-/Konturfarben und nicht beobachtbare Seiten bleiben Ablehnungen.
Für Rundung sind weiterhin zwei konsistente freiliegende Ecken je Kind nötig.
Mehr als zwei überlappende Kinder, weitere Schichten, beliebige Konturfarben
und unabhängige reale Familienabnahme bleiben offen. **Nur
SEARCH-STRUCTURE-OVERLAP-OUTLINES ist abgeschlossen; SEARCH-STRUCTURE-01
bleibt offen.** Vor weiterer realer Entwicklung sind neue Prüffamilien
zu sperren; GE0018/GE0307 bleiben bekannte Entwicklung.

## Ursache und allgemeine Korrektur

Der bisherige Vertrag schließt Überdeckung mit Konturen aus. Der Detektor
misst außerdem nur Füllung gegen Elternverlauf. Die 24 vor der Runtime-Änderung
gespeicherten CLI-Eingaben scheitern deshalb vollständig.

Die Erweiterung trennt Füllungs- und Konturdeckung gegen den lokalen Verlauf
durch zwei unabhängige Farbrichtungen. Die integrierte beobachtete Konturdeckung
liefert die Breite; die subpixelgenauen Innenkanten liefern die native
Mittelliniengeometrie. Die Rundungsmessung berücksichtigt die eigene Kontur,
ohne fremde Füllung als fehlende Eckfläche zu zählen. Eine neue Außenkonturprüfung
verlangt eigene Farbbelege außerhalb der einfachen Eltern-/Weiß-Mischung;
weißes Antialiasing allein rechtfertigt keine Kontur.

Die vorhandene geordnete Strukturagenda behält Konturen und Radien bei
`reorder`, Deduplizierung und negativer Evidenz. Die gefüllte Topologieprüfung
arbeitet auf den Mittellinien; native Konturbreiten, vollständiges Containment,
Schnittflächenfarbe und unveränderte lokale/globale Rastergates bleiben
zusätzliche Annahmebedingungen. Andere Szenenwege erhalten keine allgemeine
Freigabe für überlappende Konturen.

## Plan-B-Fehler und Vergleich der Farbhypothesen

Genau eine gekoppelte Vorlage plus 16 Größen-/Lagevarianten wurde gesichert.
Der erste vollständige Lauf besteht **16/17**; `probe_08` bleibt samt
Ausgaben und Diagnosen in `plan_b_cli/` erhalten. Es handelt sich um einen
algorithmischen Fehler bei null Registrierungen, nicht um einen Timeout.

Hypothese A: Der Median des hellsten Viertels der lokalen Konturpixel
repräsentiert die Konturfarbe. Bei der verschobenen dünnen Kontur liefert er
jedoch BGR `[228, 233, 234]` statt der beobachtbaren Farbe `[237, 240, 243]`.
Die rekonstruierte Farbmischung stimmt dadurch an keiner freien Ecke;
die Radiusprüfung verwirft den Vorschlag zurecht.

Hypothese B: Die stärksten freiliegenden Eckpixel identifizieren die Farbe,
auch wenn gerade Seiten überwiegend Mischpixel enthalten. Der Median des
hellsten Zwanzigstels liefert im selben Raster die beobachtete Konturfarbe.
Dieser allgemeine Schätzer erreicht im vollständigen neuen CLI-Lauf **17/17**
unter demselben Budget. Fremdfarben-, Radius- und Qualitätsgrenzen wurden
nicht gelockert. Ein dauerhafter Regressionstest prüft exakt die gespeicherte
verschobene Eingabe; zusätzliche Negativtests prüfen nicht identifizierbare
Farben und unzulässige Ersatzradien.

## Nachweise und Reproduktion

Alle CLI-Läufe verwenden die echte überwachte `semantic-only`-CLI, fünf
Sekunden Bildbudget und Seed 17. Der unabhängige Nachprüfer rendert die
tatsächlich gespeicherten Ausgaben erneut und prüft native Objekte,
Boundingboxen, Konturbreiten, Radien, Reihenfolge sowie lokale/globale Pixelgates.
Beide Referenzvektorwächter bleiben leer.

| Kohorte | Ergebnis |
| --- | --- |
| Zwölf vorab gesicherte eckige Szenen | vorher 0/12, endgültig 12/12 mit neutralen Namen |
| Zwölf vorab gesicherte gerundete Szenen | vorher 0/12, endgültig 12/12 mit neutralen Namen |
| Zusätzlicher Seed 927381, eckig/gerundet | 12/12 und 12/12 |
| Genau eine gekoppelte Plan-B-Vorlage und 16 Varianten | zunächst 16/17, endgültig 17/17 |
| Bestehende Überdeckungs-/Kontur-/Rundungs-/Split-/Restbildkohorten | 12/12, 12/12, 12/12, 20/20, 7/9 |

Die **63 erfolgreichen Bestandsausgaben bleiben bytegleich**. Die beiden
bekannten kontrastarmen Fehlschläge bleiben im Nenner. **379 Archivpaare und
758 Prüfsummen bleiben unverändert**; es wurde keine neue Archivkonvertierung
oder reale Familienabnahme durchgeführt.

**509 gezielte Tests bestehen**: 241 Struktur-/Kompositionsprüfungen am
endgültigen Stand und 268 zusätzliche Szenen-/Scheduler-/Evidenzprüfungen.
Die neue Suite enthält 65 Tests; frühere Teilprüfungen sind darin enthalten
und werden nicht zusätzlich gezählt. Syntaxprüfung und CLI-Hilfe bestehen.
Eine vollständige Standardsuite wurde nicht ausgeführt. CI ergänzt beide
Kontur-/Überdeckungskombinationen mit frischem Seed 391827 über die echte CLI.
Die unabhängige Nachprüfung aller 13 gespeicherten Kohorten besteht auch aus
einer separaten Kopie ausschließlich der für Git sichtbaren Dateien.

[Eingaben, tatsächliche Ausgaben und Nachprüfung](../artifacts/evaluation/overlap_outlines_v1/README.md).

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_overlap_outlines.py tests/test_overlap_composition.py tests/test_rounded_overlap_composition.py tests/test_rounded_outlines.py tests/test_rounded_composition.py tests/test_structure_search_operators.py tests/test_residual_scene_search.py
.venv/Scripts/python.exe artifacts/evaluation/overlap_outlines_v1/verify.py
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --prepare .tmp/new-overlap-outlines --outlines --rounded --seed 391827
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --inputs .tmp/new-overlap-outlines --output .tmp/new-overlap-outlines-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_overlap_composition --inputs .tmp/new-overlap-outlines --output .tmp/new-overlap-outlines-cli --verify-only --require-all
```
