# P0-Abschluss: native gerundete Rechtecke korrekt rendern

**SVG-ROUNDED-RENDERER-01**, synthetischer Teilumfang **abgeschlossen**.
Die Rendererabweichung aus dem
[gerundeten Elternteil](next_arbeitspaket_2026-11-06_rounded_parent.md)
ist korrigiert. Implementierung, eingefrorene Kontrollen und die lokale
Abnahme waren bereits vorhanden. Am 10.11.2026 wurden zwei beim Zusammenführen
zurückgesetzte Anpassungen wiederhergestellt, die aktuelle Abnahme wiederholt,
der Aufgabenstatus berichtigt und die fehlende CI-Absicherung ergänzt.

## Umsetzung und gesicherte Abnahme

Gerundete Rechtecke erhalten ausschließlich im privaten MuPDF-Eingang
einen geometrisch gleichwertigen Pfad mit zwei kubischen Béziersegmenten
je Viertelellipse. Gespeicherte SVGs behalten ihre nativen Rechtecke,
Radien, Farben, Konturen und Verläufe. Fehlende `rx`-/`ry`-Werte,
Halbseitenbegrenzung und Transformationen sind berücksichtigt.
Füllung und Verlaufsmasken verwenden dieselbe Geometrie; scharfe Rechtecke,
Kreise, Ellipsen und vorhandene Pfade behalten ihre bisherigen Pixel.

Die vor der Korrektur gesicherten librsvg-Eingaben ergeben:

- 28 Renderkontrollen: global 23/28 → 28/28, lokale Ecken 40/96 → 96/96.
- Echte primäre CLI-Kohorte: 2/12 → 12/12; Zusatzkohorte 12/12,
  eine gekoppelte Variantenkohorte 17/17.
- Beide Renderer bestehen alle 164 Elternecken der 41 neuen CLI-Ausgaben.
  Native Objekt-, Radius-, Kontur-, Verlaufs-, Eltern- und Tiefengates bleiben
  erforderlich. Der größte damalige Radiusfehler beträgt 0,2575 Pixel
  bei unveränderter 1,25-Pixel-Grenze.
- Der analytische Eckverlust bei Radius 30 beträgt 193,1417 Quadratpixel;
  MuPDF verbessert sich von 234,9529 auf 192,6824, librsvg misst 193,8471.

Gemeinsame Registrierung und Radiusstartwerte werden an Originalpixeln
gemessen. Die Konturfarbmessung und diagonale Objektboxverläufe sind
ebenfalls korrigiert. Bildbudget fünf Sekunden, acht Kinder und
96 Strukturzustände bleiben unverändert.

Die vollständigen ursprünglichen Messwerte, Prüfsummen und Grenzen stehen
im [Renderer-Nachweis](../artifacts/evaluation/rounded_renderer_v1/README.md).
Der damalige breite Testlauf bestand 1.206/1.207 Tests; ein zeitabhängiger
Acht-Objekte-Fall bestand anschließend isoliert und im Modulnachlauf.
Dieser ursprüngliche Fehler bleibt dokumentiert.

## Aktuelle Prüfung und dauerhafte Absicherung

Die Nachprüfung des zusammengeführten Stands reproduzierte einen tatsächlichen
Fehler im eingefrorenen gleichfarbigen Konturfall: Das unveränderte Modul aus
`4ff3b5ffb` liefert kein Modell, Testfehler nach 0,33 Sekunden. Es handelt sich
hier nicht um die bekannte Zeitgrenze des früheren großen Testlaufs.
Die beim Merge verlorene Messung des stärksten hellen Farbclusters ist
wiederhergestellt; mindestens fünf verschiedene beobachtete Pixel bleiben
erforderlich, andernfalls gilt die konservative Perzentilschätzung.
Die analytisch richtigen Radien verwenden wieder fünf nahe Startwerte von
95 bis 105 Prozent statt dreizehn Startwerte bis hinab zu 75 Prozent.
Beide Änderungen waren bereits im Rendererstand `56c0b9baa` enthalten.
Die unveränderten historischen Pixel bestehen danach die vollständigen
nativen und Rastergates; gezielte Nachprüfung einschließlich Budgetgegenprobe
3/3. Der unterbrochene Vorlauf bleibt getrennt vom endgültigen Lauf erhalten.
Auch eine beim Merge entfernte native Radiusgegenprobe und die aufgeweichte
Radiusmessgrenze sind wiederhergestellt: Ein global guter Rasterfit mit zwei
Pixeln falschem Radius muss unabhängig abgelehnt werden; die gemessenen
Startwerte müssen wieder innerhalb von fünf Prozent liegen. Beide Prüfungen
werden im neuen CI-Job ausdrücklich mit ihrem Testnamen aufgerufen.

Die endgültige CLI-Nachprüfung besteht 53/53 Fälle: die bisherigen
unabhängigen Kohorten 12/12, 12/12 und 17/17 sowie 12/12 für den zusätzlichen
CI-Seed `392741`. Beide Renderer bestätigen je 212/212 Elternecken.
Maximaler nativer Elternradiusfehler 0,4177 Pixel bei unveränderter
1,25-Pixel-Grenze; höchste überwachte Prozesszeit lokal 3,891 Sekunden.
Alle Eingabe- und Beschreibungsprüfsummen stimmen mit dem Vorherstand überein.
Der [aktuelle maschinenlesbare Nachweis](../artifacts/evaluation/rounded_renderer_v1/revalidation_2026-11-10.json)
bleibt getrennt von den ursprünglichen Messdateien.

Die endgültige gemeinsame Szenen-/Registrierungs-/Rendererregression besteht
1.206/1.206 Tests in 912,37 Sekunden. Die danach wiederhergestellte und die
verschärfte Radiusgegenprobe bestehen zusätzlich 2/2; ein Fall überschneidet
sich mit dem großen Lauf. Der JUnit-Knotenvergleich bestätigt damit alle
1.207 verschiedenen ursprünglichen Prüffälle. Das Kernprofil besteht 42/42.
Diese Regressions-, Radius- und Kernläufe haben Exit 0, ohne Fehler oder Überspringungen.
Keine Produktionsänderung nach diesen Abnahmen. Der GitHub-CI-Job ist
eingerichtet; ein GitHub-Lauf wurde hier nicht gestartet.
Die zusätzliche Datenhygieneprüfung besteht 12 Tests; ein Symlinktest wird
wegen fehlender Windows-Entwicklerrechte regulär übersprungen. Der kompakte
Nachweis ist ausdrücklich zur Versionierung freigegeben, während Rohdaten
unter `.tmp/` bleiben.

Der CI-Job `rounded-svg-renderer` prüft analytische Flächen, die
eingefrorenen unabhängigen Pixel, die historischen Konturfarben und den
Renderprozess. Er erzeugt zusätzlich
eine eigene Szenenkohorte mit librsvg und verlangt für die echten
CLI-Ausgaben native Objekt-/Relationsgates sowie globale, objektlokale und
alle vier Eckgates mit beiden Renderern. Der neue Vorbereitungsparameter
`--independent-reference` protokolliert die unabhängige Rendererversion;
bestehende Eingaben werden dabei nicht überschrieben.

Reproduktion in frischen Ausgabeordnern:

```powershell
.venv/Scripts/python.exe -m pytest tests/detailtests/test_rounded_renderer.py tests/detailtests/test_rendering_gradient_compatibility.py tests/test_same_paint_overlap.py -q
.venv/Scripts/python.exe -m tools.evaluate_rounded_renderer --controls tests/fixtures/rounded_renderer --report .tmp/renderer-controls-new.json --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_parent --prepare .tmp/renderer-independent-new --seed 392741 --independent-reference
.venv/Scripts/python.exe -m tools.evaluate_rounded_parent --inputs .tmp/renderer-independent-new --output .tmp/renderer-independent-cli-new --require-all
.venv/Scripts/python.exe -m tools.evaluate_rounded_renderer --inputs .tmp/renderer-independent-new --output .tmp/renderer-independent-cli-new --report .tmp/renderer-independent-audit-new.json --require-all
```

## Historische Eingaben und Abnahmegrenzen

Die alten MuPDF-Eingaben und ihre Originalausgaben bleiben bytegenau
erhalten. Ihre frühere Abnahme ist ein historischer Prüfstand. Eine erneute
CLI auf diesen Rastern benötigt falsche native Elternradien und besteht
deshalb die unabhängige Objektprüfung mit 0/41. Diese Negativkohorte wird
nicht in die neuen Erfolgsmengen eingerechnet.

## Ursprüngliche Reproduktion und Auswirkung

`tools.audit_rounded_parent_renderers` vergleicht gespeicherte synthetische
CLI-Ausgaben an ihren Originalrastern mit MuPDF und librsvg. Alle 41 Gesamtbilder
bestehen, aber nur 121/164 lokale Elternecken mit librsvg; mit MuPDF sind es
164/164. Die Gesamtfläche verdeckt die lokale Konturabweichung.

Der eingebaute analytische Kontrollfall braucht weder Konverter noch
Katalogquelle: ein gleichmäßig gefülltes natives Rechteck mit `rx=30`,
300 × 280 Pixeln und weißem Hintergrund. Soll-Eckverlust: 193,1417
Quadratpixel, MuPDF: 234,9529, librsvg: 193,8471. Die Abweichung gehört zum
vorhandenen Rendering und nicht zur neuen Topologiesuche.

```powershell
.venv/Scripts/python.exe -m tools.audit_rounded_parent_renderers --inputs .tmp/rounded-parent/inputs --output .tmp/rounded-parent/after --report .tmp/rounded-parent/renderer-replay-new.json
```

Die kompakte Gegenprobe samt Eingabe-/Ausgabehashes und allen Eckmetriken steht
in [`rounded_parent_v1`](../artifacts/evaluation/rounded_parent_v1/summary.json).
Die bestehenden synthetischen Raster und historischen Abnahmen unverändert
erhalten und als bisherigen MuPDF-Prüfstand kennzeichnen.

## Verbindlicher Lieferumfang der Abnahme

1. Gerundete native Rechtecke im vorhandenen SVG-Rasterweg an einer korrekten
   beobachteten Eckgeometrie ausrichten; Füllung, Verlauf und Kontur gemeinsam
   prüfen. Keine Sonderbehandlung nach Familie oder Bildkennung.
2. Analytische Kontrollfälle und unabhängige librsvg-Raster für mehrere Radien,
   Subpixellagen, Größen, Seitenverhältnisse, Konturbreiten und Verlaufsachsen
   **vor** der Renderingänderung sichern. Scharfe Rechtecke und vorhandene
   andere SVG-Primitive als Gegenkontrollen beibehalten.
3. Neu vorbereitete synthetische Szenen und die bereits eingefrorenen Szenen
   getrennt ausweisen. Keine stillschweigende Neugenerierung alter
   Eingabeprüfsummen oder Übernahme historischer Erfolgsmengen.
4. Echte CLI, unabhängige native Radius-/Objekt-/Relationsprüfung sowie globale
   und vier lokale Eckgates verlangen. Bestehende Grenzen, fünf Sekunden
   Bildbudget und 96 Strukturzustände bleiben verbindlich.
5. Gemeinsame Registrierung einschließlich Radiusstartwerten erneut messen.
   Keine Korrektur eines Rendererfehlers durch dauerhaft falsche native Radien.

HC0010 und Rail bleiben gesperrt und ungetestet. Nach diesem Paket folgt der
bereits erkannte nächste Kompositionsteil **SEARCH-STRUCTURE-CLIPPED-RECTANGULAR-PARENT**:
angeschnittene äußere Rechtecke anhand sichtbarer Seiten-/Eckbelege anbinden,
fehlende Grenzen ohne ausreichende Beobachtung konservativ ablehnen.
