# Image-Converter: konkrete Verbesserungsansätze (Stand 2026-05-10)

## Kurzfazit
Die aktuellen Fehlerbilder wirken nicht zufällig, sondern clustern auf bestimmte Familien (`AC0835_*`, `AC0838_*`, `AC0820_*`, `AC0870_*`) mit sehr hohen `mean_delta2`-Werten. Das spricht für systematische Modell-/Parametrisierungs-Lücken statt einzelner Ausreißer.

## Beobachtungen aus den vorhandenen Reports

Aus `pixel_delta2_ranking.csv` (57 Varianten im Snapshot) sind die schlechtesten Fälle aktuell:

- `AC0850_M.jpg` — `mean_delta2=13599.95`
- `AC0835_L.jpg` — `11170.07`
- `AC0844_S.jpg` — `10198.81`
- `AC0820_L.jpg` — `9983.60`
- `AC0842_L.jpg` — `9315.22`
- `AC0838_M.jpg` — `9225.63`
- `AC0863_L.jpg` — `9090.34`
- `AC0864_L.jpg` — `8777.11`

Dazu kommt: Viele Top-Fehler haben gleichzeitig sehr hohe `std_delta2`-Werte. Das deutet auf lokal stark falsche Bereiche hin (nicht nur global leicht daneben) – typisch für Form-/Ankerfehler, Orientation-Mismatch oder falsche Segment-/Maskenwahl.

## Verbesserungsplan (pragmatisch, mit hoher Erfolgswahrscheinlichkeit)

### 1) Family-spezifische Optimierungs-Presets statt „one-size-fits-all“

Die Reports und Tasks zeigen bereits Familien-/Prototyp-Denken (`shape_catalog.csv`, Weak-Family-Tracking). Nutze das explizit in der Suche:

- pro `prototype_group` ein eigenes Start-Parameterbündel (z. B. Threshold-Bias, Morphology-Kernel, allowed rotations),
- engeres Search-Space für bekannte stabile Familien,
- breiteres Search-Space nur für problematische Gruppen.

**Warum das hilft:** Die Top-Fehler sind clusterbasiert; globale Defaults bestrafen dann viele einfache Fälle oder treffen schwierige Familien nicht gut genug.

---

### 2) Zwei-Stufen-Scoring: erst Geometrie robust machen, dann Pixel-Feintuning

Bei hohen `std_delta2` ist häufig die Geometrie falsch. Daher Ranking der Kandidaten in zwei Schritten:

1. harte/gegewichtete Geometrie-Kriterien (IoU Formmaske, Lage des Stems/Handles, Symmetrie-Checks),
2. erst danach `mean_delta2`/`error_per_pixel` Feintuning.

**Warum das hilft:** Sonst gewinnt ein „pixelnaher, aber semantisch falscher“ Kandidat zu früh.

---

### 3) Orientation-/Mirror-Hypothesen explizit in den Kandidatenraum aufnehmen

Bei solchen Diffs ist eine häufige Ursache 180°-/Mirror-Fehlorientierung oder falsche Text-/Handle-Richtung.

- Für schwache Familien stets Kandidaten für `rotation ∈ {0, 90, 180, 270}` + Spiegelung evaluieren,
- schnelle Vorselektion via grober Maskenähnlichkeit (damit Kosten kontrollierbar bleiben).

**Warum das hilft:** Ein einzelner Orientierungssprung kann den Hauptanteil des Fehlers sofort entfernen.

---

### 4) Iterationsbudget adaptiver auf „Gap zur Bestliste“ verteilen

Die Pipeline hat bereits Quality-Pässe; ergänze Priorisierung:

- Fälle mit großem Abstand zur Bestliste bekommen mehr Budget,
- bereits gute/nahe Varianten erhalten minimales Budget,
- Abbruch bei stagnierender Verbesserung früher und aggressiver.

**Warum das hilft:** Zeit wird auf die Problemfälle fokussiert statt gleichmäßig verbrannt.

---

### 5) Diff-PNGs maschinell auswerten (nicht nur visuell): Fehlerkarten in Features überführen

Aus den vorhandenen Differenzbildern lassen sich einfache Features ableiten:

- Schwerpunkt der Fehlerpixel,
- radialer Fehler (innen/außen am Kreis),
- obere/untere Halbschale,
- Zusammenhangskomponenten und deren Orientierung.

Diese Features können direkt in Heuristiken gemappt werden („Fehler vor allem unten rechts“ ⇒ Anchor/Rotation-Hypothese A priorisieren).

**Warum das hilft:** Schnellere Diagnose, weniger Trial-and-Error.

---

## Priorisierte nächste Schritte (konkret für die nächsten 1–2 Tage)

1. **Top-10-Schwachfälle fixen statt Full-Range optimieren.**
   Zielmenge aus `pixel_delta2_ranking.csv` ziehen und nur diese in einem fokussierten Debug-/Optimierungslauf nutzen.
2. **Family-Presets + Orientation-Hypothesen nur für diese Zielmenge aktivieren.**
   Minimiert Risiko für Regression in bereits guten Familien.
3. **Vorher/Nachher-Report automatisieren** (`mean_delta2`, `std_delta2`, Qualitätsentscheidung, Laufzeit).
4. **Nur Verbesserungen übernehmen** (wie bereits im Quality-Workflow angelegt), Regressionen automatisch verwerfen.

## Empfehlung

Wenn du gerade ratlos bist, ist der beste Hebel **nicht** „noch mehr globale Parameter drehen“, sondern eine **gezielte Weak-Family-Offensive**: pro Problemfamilie kurze, reproduzierbare Experimente mit family-spezifischen Presets + Orientation-Sweep und striktem Vorher/Nachher-Gate.
