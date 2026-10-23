# SEARCH-STRUCTURE-01: Rundung und helle Konturen zusammensetzen

Ausgangsstand: `00dfb2cc7` (`main`).
Branch: `codex/search-structure-rounded-outlines-2026-10-23`.
Extrahiert aus dem höchsten offenen P0-Paket in
[open_tasks.md](open_tasks.md) gemäß der
[verbindlichen Rangfolge](weakness_review_2026-10-23.md).

## Abgegrenzte Aufgabe

Den im vorherigen Rundungsbaustein ausdrücklich ausgeschlossenen Vertrag
„gerundete Rechteckkinder und helle Konturen“ im vorhandenen Verlaufskreisweg
unterstützen. Die gemeinsamen Zerlegungen, Add/Remove/Replace, negative Evidenz,
Rendercache, Scheduler und Bildzeitaufsicht weiterverwenden. Keine neue
Familienvorlage, Referenzgeometrie oder Katalogkennung einführen.

Dieser technische Teil ist abgeschlossen. SEARCH-STRUCTURE-01 bleibt für
Überdeckungen, weitere Schichten und unabhängige reale Übertragung offen.
Alle neuen Eingaben sind synthetisch. Die vorgeschriebene Sperrung und
unabhängige Markierung weiterer realer Prüffamilien bleibt vor realer
Runtime-Entwicklung erforderlich; GE0018/GE0307 bleiben Entwicklung.

## Umsetzung und Fehleranalyse

Der Parser bindet die Rundung weiterhin genau an die quantifizierten Rechtecke
und verarbeitet sämtliche übrigen Aussagen unverändert. Er erlaubt jetzt
zusätzlich die bereits vorhandene Aussage über helle Konturen aller Formen.
Native SVG-Rechtecke tragen `rx`, Konturfarbe und Konturbreite; native
Kreiskinder können daneben im selben Inventar stehen.

Zwei überprüfte Ansätze:

1. Die vorhandene Füllung-/Konturprojektion ohne örtlichen Hintergrund zu
   verwenden liefert falsche Eckradien. Der dunklere Verlauf außerhalb der
   Ecken wird als Füllungsanteil mitgezählt. Im ersten gezielten Versuch
   scheitern neun von 28 Prüfungen, darunter die fehlende Kontur.
2. Füllung und Kontur gegen den örtlichen Verlauf als getrennte beobachtete
   Farbmischungen zu schätzen trennt die Eckfläche von der Hintergrundfarbe.
   Die integrierte zentrale Konturdeckung liefert ihre Breite; die fehlende
   innere Eckfläche liefert den inneren Radius. Zusammen mit der halben
   Konturbreite ergibt sich der native Eckradius. Auch der Elternkreis erhält
   seine eigene aus dem äußeren Rasterring gemessene Konturbreite.

Die zweite Lösung behebt die positiven Fälle. Zusätzliche Gegenproben mit
genau einer dunklen Kontur deckten dennoch falsche Freigaben auf: Ein
Konturvorschlag konnte die benachbarte Hintergrundfarbe verwenden, während
die bisherigen lokalen Rastergrenzen die kleine Abweichung tolerierten.
Die endgültige Erkennung verlangt deshalb beobachtete helle Randpixel über
dem örtlichen Elternverlauf und weist einen dunklen äußeren Kreisrand direkt
zurück. Diese Prüfungen verschärfen die Vorschlagsbindung; die bisherigen
Objekt-, Relations-, lokalen und globalen Qualitätsgrenzen bleiben unverändert.

Nicht unabhängig identifizierbare Farbmischungen werden konservativ abgelehnt.
Insbesondere ist damit keine allgemeine Abnahme grauer oder kontrastarmer
Konturen verbunden. Leichte beobachtbare Rundung, ein axialer Verlaufskreis
und getrennte native Kinder bleiben der begrenzte Szenenumfang. Der Split-Weg
bleibt für Konturen weiterhin deaktiviert; Überdeckung wird nicht freigegeben.

## Nachweis und Reproduktion

Zwölf Eingaben samt Prüfsummen, Beschreibungen und unabhängigen nativen
Objektmarkierungen wurden vor der Runtime-Änderung gespeichert. Vorher und
nachher verwendet die echte überwachte `semantic-only`-CLI fünf Sekunden
Bildbudget und Suchseed 17. Die finale Wiederholung nutzt neutrale Dateinamen.

| Kohorte | Vorher | Endstand |
| --- | --- | --- |
| Zwölf eingefrorene Fälle, beide Verlaufsachsen, ein/zwei/vier/sechs Rechteckkinder und verschiedene Konturbreiten | 0/12 | 12/12 |
| Zwölf zusätzliche synthetische Fälle mit anderem Geometrie-/Farbseed | – | 12/12 |
| Genau eine gekoppelte Plan-B-Vorlage, Original plus 16 Größen-/Lagevarianten | – | 17/17 |
| Bisherige gerundete Szenen ohne Konturen | 12/12 | 12/12 |
| Bekannte Split-/Operatorfälle | 20/20 | 20/20 |
| Bekannte Restbildfälle einschließlich zweier kontrastarmer Fehlversuche | 7/9 | 7/9 |

Der unabhängige Nachprüfer liest die tatsächlichen nativen SVG-Objekte und
prüft Anzahl, Formklasse, Boundingbox, Eckradius, Konturbreite, Verlaufsachse,
Zeichenreihenfolge, Objektregionen und das gesamte Originalraster. Beide
Referenzvektor-Zugriffswächter bleiben leer. CLI-Berichte enthalten die
Runtime-Prüfsummen. Zusätzliche Tests prüfen fehlende und dunkle Konturen
an einzelnen Objekten, eckige Ersatzformen, Textur, zusätzliche/fehlende
Instanzen, falsche Lage/Anzahl, unbekannte Aussagen, Remove, gemischte
Formklassen, nicht identifizierbare Farben und Budgetablauf vor Registrierung.

Eingaben, tatsächliche Ausgaben und maschinenlesbare Abschlussprüfungen:
[`artifacts/evaluation/rounded_outlines_v1/`](../artifacts/evaluation/rounded_outlines_v1/README.md).
Die 379 gespeicherten Archivpaare bleiben mit 758 unveränderten Prüfsummen
erhalten. Das ist eine Hashprüfung, keine Archiv-Neukonvertierung oder neue
Pixelabnahme. Alle 39 bisherigen erfolgreichen CLI-Ausgaben der drei
Regressionskohorten sind bytegleich zum vorherigen Teilabschluss.
**422 gezielte Szenen-/Such-/Deadline-/ID-Tests bestehen**, darunter alle
**35 neuen Tests** (172,45 Sekunden). Syntax, CLI-Hilfe und die Runtime-ID-Prüfung
mit null Katalog-IDs bestehen; Whitespace ist mit den bestehenden
Windows-Zeilenenden geprüft. Die vollständige historische Gesamtsuite wurde
nicht erneut ausgeführt.
Die neue CI-Aufgabe wiederholt die neuen Tests und zwölf weitere synthetische
CLI-Fälle mit unabhängiger Nachprüfung.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_rounded_outlines.py
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --prepare .tmp/outlined-inputs --outlines --seed 942817
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs .tmp/outlined-inputs --output .tmp/outlined-cli --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_composition --inputs .tmp/outlined-inputs --output .tmp/outlined-cli --verify-only --require-all
```
