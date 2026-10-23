# Nächstes Arbeitspaket – GE1410_L und neue AC05-Samples Run ABH (2026-07-31)

Run ABH arbeitet nach Run ABG den dokumentierten nächsten Schritt der aktiven
Plan-B-Rotation ab und erfasst zugleich die drei neu gelieferten Samples als
prüfbare, katalogfreie Folgeaufgaben. Die Samples werden nicht als fertige
Konverter-Ausgabe behandelt: Sie dienen als Qualitätsreferenzen und als
Generalisierungsfälle für gemeinsam nutzbare Primitive.

## 1) Nächste dokumentierte Aufgabe: GE1410_L

- Die allgemeinen `PolygonPath`-Punkt- und Stroke-Width-Probes erhalten die
  zusätzliche Zwischenstufe `±0.0000000000023283064365386962890625`.
- Ein Helper-Test prüft Punkt und Konturbreite über den normalen sequenziellen
  Optimierer und akzeptiert Kandidaten nur bei sinkendem Fehler.
- Die Erweiterung enthält keine Bild-ID und ist damit auch für Diagramme,
  Dreiecke und freie Konturen ausserhalb von `GE1410_L` nutzbar.

## 2) Drei sample-basierte Plan-B-Aufgaben

1. **AC0502_1L_sia – Struktur statt Sample-Kopie:** Diagonalverbindung,
   Kreisanker, rotes Rechteck und zwei weisse Diagonalen als getrennte
   Primitive erkennen. Baseline des reproduzierbaren Roundtrips:
   `delta2_output_vs_sample=497.845640`.
2. **AC0502_1M_sia – Grössengeneralisierung:** dieselbe Topologie bei 60×30 aus
   normalisierten Relationen erzeugen; keine zweite ID-spezifische Geometrie.
   Baseline: `delta2_output_vs_sample=465.142682`.
3. **AC0538_1L_sia – Variantenklassifikation:** den gemeinsamen linken
   Diagonal-/Kreisanker wiederverwenden, das rechte Feld aber als graurahmiges
   rotes Rechteck mit weisser Stufenkurve unterscheiden. Baseline:
   `delta2_output_vs_sample=1629.625242`; der Lauf bleibt wegen der fehlenden
   fachlichen Beschreibung zunächst korrekt als `manual_review` markiert.

Die Baselines stammen aus `tools/plan_b_roundtrip.py`; keine der Aufgaben darf
durch Einbetten oder unverändertes Kopieren des Sample-SVGs als gelöst gelten.
Priorität hat zunächst der gemeinsame AC0502-L/M-Familienpfad, danach die
AC0538-Klassifikation.

## 3) Plan-B-/Perception-Lerneffekt

`GE1410_L` bleibt auf Seed-Ebene `generalisiert`; Run ABH erweitert nur dessen
katalogfreien PolygonPath-Registrierungsraum. Für die neuen Samples lautet die
Perception-Frage, ob `line`, `circle`, `rectangle` und `polygon_path` die
Topologie ohne Dateinamenwissen abdecken. AC0502 L/M sind wegen der gemeinsamen
skalierbaren Primitive als `generalisiert` zu entwickeln. AC0538 ist bis zur
fachlichen Klassifikation `noch nicht erkannt`; die Sample-Kopie ist lediglich
Plan B und kein Wahrnehmungserfolg.

## 4) Ergebnis / nächster Schritt

Der dokumentierte GE1410_L-Feinschritt ist auf Code- und Helper-Test-Ebene
abgeschlossen. Alle drei neuen Samples besitzen jetzt reproduzierbare
Plan-B-Baselines und konkrete Akzeptanzrichtungen. Das nächste Paket soll den
gemeinsamen AC0502-L/M-Geometry-IR-Seed implementieren und dabei Laufzeit sowie
Qualität gegen beide Baselines berichten, statt weitere Varianten von Hand
nachzuzeichnen.
