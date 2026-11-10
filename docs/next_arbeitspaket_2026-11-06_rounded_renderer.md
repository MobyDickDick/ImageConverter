# Nächstes P0-Paket: native gerundete Rechtecke korrekt rendern

**SVG-ROUNDED-RENDERER-01**, Status **Planned**. Neu reproduzierte
Rendererabweichung aus dem [gerundeten Elternteil](next_arbeitspaket_2026-11-06_rounded_parent.md).
Sie hat gemäß der verbindlichen Reihenfolge Vorrang vor weiterer Komposition.

## Reproduktion und Auswirkung

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

## Lieferumfang und Abnahme

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
