# Grauverlauf mit Rahmen: allgemeine Korrektur, 12.11.2026

Die vollständige Wiederholung des exportierten Workbench-Versuchs verbessert
sich von **7/17 auf 17/17**. Das Original und alle 16 Varianten bestehen
unverändert strenge Pixel-, Kontur-, Überlappungs-, Größen- und Komplexitätsgrenzen.
Die ursprüngliche Beschreibung ohne zusätzlichen Rechteck-Satz besteht auf
denselben Rasterbytes ebenfalls **17/17**. Sechs zusätzliche synthetische Fälle
mit anderen Größen, Grautönen, Achsen und angeschnittenen Rahmen bestehen **6/6**.
Alle 40 gespeicherten Ausgaben bestehen außerdem die unabhängige Darstellung
mit librsvg und die lokalen Profilprüfungen.

## Korrektur

- Die gemeinsame Sprachnormalisierung erkennt Farb-/Farbenübergang und
  Graustufenübergang einschließlich `ue`-Schreibweise. Die Graustufeninformation
  und zitierte Beschriftungen bleiben erhalten.
- Der flache Rechteckfit weist beschriebene Verläufe zurück. Ein Rastertest
  auf systematische Profiländerung verhindert zusätzlich, dass ein breites
  Glanzband ohne Verlaufshinweis als flache Innenfläche ausgegeben wird.
- Der vorhandene präzise Vier-Stopp-Verlaufsfit akzeptiert freie Beschreibungen
  mit eindeutiger Achse, Graustufen, Rahmen und Helligkeitsmaximum. Unpassende
  zusätzliche Objekte, widersprüchliche Achsen und falsche Maximallage werden
  weiterhin abgewiesen. Variantenformulierungen verändern die Objektaussagen nicht.
- Die Rahmenfarbe wird aus dem dunklen beobachteten Randanteil geschätzt;
  abgeschnittene Kanten und weißes Padding verhindern den Fit nicht mehr.
  Rechteckgrenzen können knapp außerhalb des Rasters liegen und werden gemeinsam
  mit Konturbreite, Farben und Stopp-Lagen registriert.
- Die Initialisierung des Verlaufs schließt die Antialiasing-Zone des Rahmens
  aus. Das verhindert, dass die Randfarbe als zusätzlicher Farbübergang modelliert
  wird. Die bisherige breitere Profilprüfung und sämtliche Qualitätsgrenzen
  bleiben bestehen.
- Ein vollständiger Verlaufstext aktiviert den Fit auch dann, wenn die
  allgemeine Formenerkennung mangels Rechteck-Nomen `insufficient_description`
  meldet. Andere unvollständige Beschreibungen erhalten diese Ausnahme nicht.

Die Runtime verwendet Raster und Beschreibung, keine neuen Katalogkennungen,
SVG-Vorlagen oder abgeschriebenen Geometriewerte. Jede Ausgabe enthält genau
ein Rechteck mit vier kontinuierlichen Verlaufsstopps und keine Rastereinbettung.

## Abnahme und Belege

Der ZIP-Export aus `C:/Users/marku/Downloads/plan-b-workbench.zip` bleibt unverändert.
`tools.evaluate_framed_panel_recheck` kopiert die 17 PNGs bytegleich, prüft ihre
gespeicherten Hashes und erzeugt die Beschreibungstabelle aus den Daten. Es
führt keine Befehle aus dem Archiv aus. Die echte CLI erhält ausschließlich
Raster und Text unter neutralen Namen mit dem bestehenden SVG-Zugriffsaudit.

| Kohorte | CLI | librsvg | max. RGB-MSE | min. Kontur | min. IoU |
|---|---:|---:|---:|---:|---:|
| Exportbeschreibung, Seed 64217 | 17/17 | 17/17 | 0,000270 | 0,768234 | 0,950000 |
| Ursprüngliche Beschreibung, Seed 64217 | 17/17 | 17/17 | 0,000278 | 0,766657 | 0,950000 |
| Zusätzliche Fälle, Suchseed 816327 | 6/6 | 6/6 | 0,000035 | 0,918833 | 0,970618 |

64 Iterationen und 60 Sekunden Prozesslimit je Fall bleiben unverändert.
Alle 40 Fälle haben null verbotene SVG-Zugriffe und keine technischen Fehler.
Bei beiden 17er-Kohorten beträgt der maximale unabhängige Profilfehler
3 Graustufen, der Spitzenfehler 2; Grenzen bleiben 4 beziehungsweise 3.

Die lokalen Prozesszeiten summieren sich auf 215,154 Sekunden für die
Exportbeschreibung, 219,531 für den ursprünglichen Text und 63,032 für die sechs
Zusatzfälle. Die ausgewählten Panel-Registrierungen zählen 17.908, 18.053 und
5.413 tatsächlich gerenderte Kandidaten. Das sind lokale Messungen während
paralleler Prüfungen, kein kontrollierter Laufzeitvergleich.

`summary.json` enthält kompakte Einzelmetriken, Eingabe-/Ausgabehashes,
Quellfingerabdruck und Renderzählungen. `before_after.png` zeigt das Original
neben der alten flachen und der neuen nativen Verlaufsrekonstruktion. Unter
`accepted_cli`, `initial_wording_cli` und `accepted_independent_cli` bleiben
vollständige Berichte, PNGs, native SVGs, Logs und Zugriffsaudits lokal erhalten.

Die feste Rekonstruktionsreferenz ist immer das vorhandene Eingabe-PNG.
Die ursprüngliche SVG wird ergänzend unabhängig gerendert; die bekannten kleinen
Unterschiede historischer Rasterisierung sind separat erfasst und ersetzen
die eingefrorenen Prüfbytes nicht.

## Hypothesenvergleich und Regressionen

Die reine Freischaltung des alten präzisen Fits über bereits unterstützte
Formulierungen deckt nur 8/17 Raster ab: abgeschnittene Rahmen scheitern an
der Randprüfung. Die erste gemeinsame Rahmen-/Verlaufsregistrierung besteht
zwar alle Exportfälle, scheitert aber noch an allen sechs Zusatzfällen. Die
Trennung von Rahmen-Antialiasing und Verlaufsinitialisierung behebt diese
zusätzliche Ursache. Frühere Zwischenstände bleiben lokal erhalten.

269 gezielte Tests bestehen für gerahmte und axiale Verläufe, echte flache
Rechteckflächen, Sprache/Negation, Runtime-Zuordnung, Plan-B-Abnahme und
Workbench einschließlich HTTP- und Prozessprüfungen. Neue Regressionen prüfen
freie Formulierungen, Erhalt des Graustufenhinweises, angeschnittene Rahmen
beider Achsen, ausgeschlossene zusätzliche Objekte, Maximallage und die
Modellzuordnung ohne ausdrücklich genanntes Rechteck. Die bisherigen
positiven JPEG- und synthetischen flachen Rechteckfälle bestehen weiterhin.

Die Korrektur ist bei neuen Workbench-Versuchen wirksam: Jeder Versuch startet
einen neuen Python-Konverterprozess. Historische Versuche bleiben als Belege
erhalten. Die Abnahme gilt für diese Verlaufsfamilie, nicht den ganzen Katalog.

## Wiederholung

Neue Ausgabeverzeichnisse verwenden; vorhandene Versuche werden nicht überschrieben.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_framed_panel_recheck --archive C:/Users/marku/Downloads/plan-b-workbench.zip --output-dir .tmp/panel_export_replay
.venv/Scripts/python.exe -m tools.evaluate_framed_panel_recheck --archive C:/Users/marku/Downloads/plan-b-workbench.zip --description-file artifacts/evaluation/ac0vr2_zl_panel_2026-11-12_description.txt --output-dir .tmp/panel_original_prose_replay
.venv/Scripts/python.exe artifacts/evaluation/framed_panel_recheck_v2/generation.py --output-dir .tmp/panel_independent_replay
.venv/Scripts/python.exe artifacts/evaluation/framed_panel_recheck_v2/summarize.py
```
