# Untersuchung: Warum die SVG-Konvertierung „harzig“ ist (Stand 2026-04-12)

## Ziel
Diese Notiz untersucht systematisch, warum die Konvertierung (insb. AC08xx) häufig langsam ist und trotz Iterationen nur schwach konvergiert.

## Datengrundlage
- Validierungs-Logs und Metriken aus:
  - `src/artifacts/converted_images/reports`
  - `artifacts/converted_images/reports`
- Maschinenlesbare Auswertung: `docs/convergence_bottleneck_analysis.json`
- Laufzeit-Stichproben (lokal):
  - `AC0838_*` (3 Varianten): ~22.1s
  - `AC0223_*` (6 Varianten): ~34.2s

## Kernergebnisse

### 1) Für AC08xx ist die Suche oft stark eingeschränkt
Aus 71 ausgewerteten AC08-Validierungslogs:
- `global-search` wurde in **53.5%** der Fälle übersprungen.
- Breiten-Bracketing wurde in **69.0%** der Fälle übersprungen.
- Stagnation/Frühabbruch trat in **54.9%** der Fälle auf.
- Median Verbesserungsquote (erste vs. beste Rundenfehler): nur **~8.9%**.

Interpretation: Der Optimierer arbeitet oft mit zu wenigen freien Freiheitsgraden, um aus lokalen Plateaus herauszukommen.

### 2) Die Software setzt für AC08 bewusst starke Geometrie-/Stil-Locks
Im AC08-Finalisierungsblock werden u.a. gesetzt:
- `lock_stroke_widths = True`
- häufig `lock_circle_cx = True`, `lock_circle_cy = True`
- Re-Ankerung auf Template-Zentrum

Das erhöht semantische Stabilität, reduziert aber Suchraum und Korrekturpotenzial bei abweichenden Vorlagen.

### 3) Global Search hat eine harte Aktivierungsschwelle
Global-Search wird nur ausgeführt, wenn mindestens 4 aktive (nicht gelockte) Parameter übrig sind. Sind viele Parameter gelockt, ist Global-Search automatisch aus.

### 4) Zusätzliche AC08-Adaptiv-Logik ist derzeit deaktiviert
`activateAc08AdaptiveLocksImpl` / `releaseAc08AdaptiveLocksImpl` geben aktuell immer `False` zurück. Damit fehlt ein Mechanismus, der Locks dynamisch lösen oder gezielt setzen könnte.

### 5) Rechenzeit pro Symbol ist strukturell hoch
Jeder Kandidat braucht SVG-Render + Pixelvergleich. In der Render-Pipeline wird pro Render-Versuch aktiv aufgeräumt (`gc.collect()`), was robust, aber teuer ist. Dazu kommen viele Kandidatenbewertungen pro Runde.

## Warum konvergiert es oft nicht „zur befriedigenden Lösung“?

Die Ursache ist **nicht nur** eine falsche Metrik, sondern eine Kombination:

1. **Über-Restriktion (dominant):**
   Bei AC08 sind wichtige Parameter fixiert; dadurch fehlt Beweglichkeit im Suchraum.

2. **Schwellwert-/Gating-Effekte:**
   Global Search fällt weg, sobald zu wenige aktive Parameter verbleiben.

3. **Plateau-Situation:**
   Die verbleibenden Parameter liefern häufig nur kleine Fehlerreduktionen; danach Stagnation.

4. **Metrik-Risiko (sekundär):**
   Pixel-Fehler kann anti-aliased Kanten übergewichten. Das ist relevant, aber nicht allein ursächlich.

5. **Beschreibungsqualität (sekundär):**
   Sprache hilft bei Semantik/Topologie, aber nicht ausreichend für präzise Mikrotuning (Subpixel-Lage, Kantenglättung, Strichstärke-Anmutung).

## Zu den genannten Serien AC0823 / AC0023
- In den verfügbaren Reports dieser Arbeitskopie wurden **keine** `AC0823*`- bzw. `AC0023*`-Validierungslogs gefunden.
- `AC0223` ist vorhanden; dort wurden zwar mehr Runden gefahren (Median 6), aber die relative Fehlerverbesserung war praktisch 0% im aktuellen Snapshot.

## Realistisches Optimierungspotenzial (priorisiert)

### A) Zweiphasen-Strategie statt durchgehender harter Locks (höchster Hebel)
1. **Phase 1 (semantisch sicher):** harte Locks wie heute.
2. **Phase 2 (gezielte Freigabe):**
   - nur bei stagnation/high-error
   - temporär `cx/cy` oder einzelne Width-Parameter in engen Korridoren freigeben
   - danach wieder semantisch validieren und ggf. rollback.

Erwartung: deutlich bessere Konvergenz bei „knappen“ Fällen ohne generellen Qualitätsverlust.

### B) Global-Search-Gating absenken/erweitern
- Statt `>=4` aktive Parameter: adaptiv auch bei 2–3 Parametern eine reduzierte Joint-Suche erlauben.
- Alternativ: Fallback auf kleine 2D/3D-Joint-Suche, wenn Global-Search nicht greift.

### C) Multi-Objective-Score (statt reinem Pixel-Druck)
- `score = w1*pixel_error + w2*geometry_penalty + w3*semantic_penalty`
- Kanten-/Konturgewichtung weniger aggressiv, dafür Formtreue stärker.

### D) Evaluate-Cost senken
- Render-Memoization pro Parameter-Fingerprint.
- Batched Candidate Evaluation (wenn möglich) und sparsame GC-Aufrufe.
- Frühabbruch-Kriterien pro Runde schärfen.

### E) Bessere Problemklassifizierung vor Optimierung
- „leicht“, „grenzwertig“, „schwer“ aus Initialfit ableiten.
- Nur schwierige Fälle bekommen teure Suchphasen.

## Fazit
Die „harzige“ Dynamik ist im Kern ein **Systemdesign-Effekt**: starke, absichtlich gesetzte AC08-Restriktionen plus harte Search-Gates plus teure Pixel-basierte Evaluierung. Das ist robust für Semantik, aber limitiert Feinkonvergenz. Das größte realistische Potenzial liegt in einer kontrollierten, temporären Suchraum-Öffnung bei Stagnation – nicht im vollständigen Entfernen der Restriktionen.
