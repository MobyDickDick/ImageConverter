# AC08-Artefaktanalyse aus `artifacts/converted_images`

## Datengrundlage

Diese Auswertung basiert auf den aktuell erzeugten AC08-Artefakten in
`artifacts/converted_images/converted_svgs/`, den per-Datei-Logs in
`artifacts/converted_images/reports/*_element_validation.log` sowie den
aggregierten Reports `pixel_delta2_ranking.csv`, `pixel_delta2_summary.txt`,
`quality_tercile_passes.csv`, `variant_harmonization.log` und
`strategy_switch_template_transfers.csv`.

Der betrachtete Snapshot enthält 50 AC08-SVGs aus 18 Familien. Davon sind 20
Dateien als `_failed` markiert. Besonders auffällig ist, dass die Familien
`AC0800`, `AC0811`, `AC0812`, `AC0813` und `AC0814` in allen drei Größen
fehlschlagen, während Problemfälle wie `AC0831`, `AC0836`, `AC0838` und
`AC0870` nur einzelne Varianten betreffen.

## Kurzfazit

1. **Das Hauptproblem ist derzeit Semantik-/Strukturerkennung, nicht nur Feintuning.**
   Ein großer Teil der `_failed`-Dateien scheitert bereits an der elementaren
   Erkennung von Kreis, horizontalem Strich oder Text.
2. **Die Tercile-/Qualitätspässe sind noch kein verlässlicher Verbesserer.**
   Im aktuellen Snapshot liegt `images_with_mean_delta2_le_threshold=0`, und die
   meisten protokollierten Passes werden als `rejected_regression` verworfen.
3. **Variantentransfers funktionieren punktuell, aber nicht familienweit.**
   Es gibt nur drei dokumentierte erfolgreiche Template-Transfers; die
   Harmonisierung zwischen Varianten scheitert fast überall.
4. **Kleine Varianten (`_S`) bleiben überproportional instabil.**
   Mehrere `_S`-Fälle gehören entweder zu den schlechtesten Pixel-Deltas oder
   enden direkt im Semantikfehler.

## Beobachtungen aus den Reports

### 1. Hoher Anteil an echten Semantikfehlern

Die fehlgeschlagenen Familien zerfallen in klar erkennbare Muster:

- **`AC0811`–`AC0814`:** alle Varianten melden `semantic_mismatch`, obwohl die
  Audit-Ausgabe bereits `SEMANTIC: Kreis ohne Buchstabe` bzw. die korrekte
  Connector-Ausrichtung ableitet. Gleichzeitig wird weiter ein nicht robuster
  Textnachweis bemängelt. Das deutet darauf hin, dass die Family-Regel zwar im
  Audit sichtbar ist, aber in der nachgelagerten Bewertung noch nicht
  vollständig priorisiert wird.
- **`AC0831_M`, `AC0836_L`, `AC0870_S`:** hier wird jeweils ein zusätzlicher
  horizontaler Strich erkannt, der laut Beschreibung nicht vorhanden sein
  sollte. Das spricht eher für Übererkennung oder Maskenartefakte als für
  fehlende Suchraumfreiheit.
- **`AC0833_S`, `AC0838_S`:** beide scheitern daran, dass ein horizontaler
  Strich laut Beschreibung erwartet wird, im Bild aber nicht robust erkannt
  wird. Das ist ein starkes Indiz für eine zu fragile Linienerkennung bei
  kleinen oder kontrastschwachen Varianten.
- **`AC0800_*`:** hier wird ein Kreis erkannt, der semantisch nicht erwartet
  wird. Auch das deutet auf ein Klassifikationsproblem der Primitive hin.

### 2. Qualitätsoptimierung verschlechtert oft statt zu helfen

Der aggregierte Report `pixel_delta2_summary.txt` zeigt für 31 ausgewertete
Bilder null Treffer unter dem dokumentierten Schwellenwert (`18.0`). Gleichzeitig
führt `quality_tercile_passes.csv` fast ausschließlich `rejected_regression` auf.

Besonders starke Rückschritte nach Qualitätspässen:

- `AC0835_L`: `5724.55 -> 13716.39`
- `AC0835_M`: `5001.25 -> 12365.55`
- `AC0835_S`: `5685.85 -> 10382.03`
- `AC0820_S`: `4272.32 -> 10370.04`
- `AC0870_M`: `6105.56 -> 11222.37`
- `AC0882_S`: `5890.86 -> 10729.97`

Das Muster ist auffällig: Der Optimierungspfad verschlechtert besonders häufig
Familien mit Text und/oder enger Geometrie. Daraus folgt, dass der Suchpfad
noch zu aggressiv in Radius-, Connector- oder Text-Skalierung eingreift, obwohl
bereits eine brauchbare Ausgangslösung existiert.

### 3. Variante-zu-Variante-Transfers sind nützlich, aber bisher zu selten

`strategy_switch_template_transfers.csv` enthält nur drei erfolgreiche Fälle:

- `AC0832_S <- AC0832_L`
- `AC0836_M <- AC0831_L`
- `AC0836_S <- AC0831_L`

Die Logik funktioniert also grundsätzlich, aber sie wird noch nicht breit genug
aktiv oder findet zu wenige kompatible Spender. Zusammen mit dem
`variant_harmonization.log` ergibt sich ein klares Bild: Fast alle Familien
bleiben über ihrer jeweiligen Basisfehlerschwelle und werden daher nicht
harmonisiert.

Daraus folgt: Template-Transfers sollten nicht nur als späte Ausnahme, sondern
früher als gezielte Initialisierung für geometrisch ähnliche AC08-Familien
verwendet werden.

### 4. Kleine Varianten bleiben der größte Risikobereich

Unter den schwächsten Pixel-Ergebnissen tauchen mehrere kleine Varianten sehr
weit oben auf, z. B. `AC0882_S`, `AC0835_S` und `AC0820_S`. Zusätzlich schlagen
`AC0833_S`, `AC0838_S` und `AC0870_S` bereits semantisch fehl.

Das bestätigt zwei praktische Schlussfolgerungen:

- Für `_S`-Varianten reicht ein allgemeiner AC08-Modus nicht aus.
- Die Primitive-Erkennung für kleine Kreis-/Linienkombinationen benötigt
  robustere, größenabhängige Toleranzen.

## Konkrete Schlüsse für die Verbesserung des Konverters

## Priorität A – Semantik-Gate nach Family-Regeln härten

Für `AC0811`–`AC0814` ist der kritischste Punkt, dass die Logs weiterhin einen
Textmismatch melden, obwohl die Audit-Daten die Family-Semantik bereits korrekt
herleiten. Der Konverter sollte deshalb nach der Family-Klassifikation einen
harten Ausschluss nicht erwarteter Textelemente anwenden.

**Empfohlene Maßnahme:**
- Nach erfolgreicher Family-Regelableitung ein verbindliches
  `expected_text_presence = false` setzen.
- Textdetektoren in diesen Familien nur noch als Warnsignal loggen, nicht mehr
  als Blocking-Fehler werten.
- Zusätzlich eine Debug-Zeile ausgeben, die explizit dokumentiert, welche
  Semantikquelle die finale Bewertung entschieden hat.

## Priorität B – Primitive-Erkennung gegen Über- und Untererkennung stabilisieren

Mehrere Fehlfamilien sind keine echten Geometrieprobleme, sondern Fehler bei der
Existenzprüfung einzelner Primitive:

- falscher Kreisfund bei `AC0800_*`
- falscher Horizontalstrich bei `AC0831_M`, `AC0836_L`, `AC0870_S`
- fehlender Horizontalstrich bei `AC0833_S`, `AC0838_S`

**Empfohlene Maßnahme:**
- Kreis- und Linienkandidaten mit einer family-/variantenspezifischen
  Mindestfläche und Mindestlänge absichern.
- Für `_S`-Varianten Morphologie und Kontrastschwellen getrennt parametrieren.
- Primitive nicht nur binär vorhanden/nicht vorhanden werten, sondern mit einem
  Confidence-Score versehen und bei Grenzfällen zunächst als `uncertain`
  behandeln.

## Priorität C – Qualitätspässe konservativer machen

Die Reports zeigen, dass der Qualitäts-/Tercile-Pfad aktuell überwiegend als
Regressionsgenerator wirkt.

**Empfohlene Maßnahme:**
- Qualitätspässe früher abbrechen, wenn sich `mean_delta2` in zwei aufeinander
  folgenden Runden verschlechtert.
- Den Pass gar nicht erst starten, wenn die Basiskonfiguration bereits in einem
  „stabil, aber nicht gut genug“-Fenster liegt und der Kandidatenraum nur noch
  kosmetische Änderungen zulässt.
- In den Reports zusätzlich die betroffene Parametergruppe markieren
  (`circle`, `connector`, `text`, `color`), damit Rückschritte schneller einer
  Ursache zugeordnet werden können.

## Priorität D – Erfolgreiche Spenderfamilien systematisieren

Die drei erfolgreichen Transfers zeigen, dass geometrisch ähnliche Familien sich
gegenseitig helfen können.

**Empfohlene Maßnahme:**
- Eine feste AC08-Spender-Matrix dokumentieren und im Initialisierungspfad
  nutzen, z. B. linke Connector-Familien untereinander sowie visuell ähnliche
  L-/M-/S-Klassen.
- Bei `_S`-Varianten gezielt mit herunterskalierten L- oder M-Templates starten,
  bevor freie Optimierungsschritte beginnen.
- Transfererfolg separat messen: „Start mit Donor vs. Start ohne Donor“.

## Priorität E – Kleine Varianten separat reporten

Die aktuelle Berichtsstruktur mischt starke und schwache Varianten. Für die
weiteren Verbesserungszyklen wäre ein eigener Small-Variant-Report hilfreich.

**Empfohlene Maßnahme:**
- Einen zusätzlichen Report `ac08_small_variant_summary.csv` erzeugen.
- Darin pro `_S`-Variante erfassen:
  - Primitive-Confidences,
  - aktivierte Small-Variant-Guards,
  - finalen Abbruchgrund,
  - Donor-/Fallback-Nutzung,
  - Delta zum besten L-/M-Template derselben Familie.

## Empfohlene nächste Arbeitsreihenfolge

1. **Semantik-Gate für `AC0811`–`AC0814` korrigieren** und danach diese vier
   Familien komplett re-runnen.
2. **Primitive-Erkennung für `_S`-Varianten härten**, zunächst an `AC0833_S`,
   `AC0838_S` und `AC0870_S`.
3. **Qualitätspass konservativer machen** und die Top-Regressionsfamilien
   `AC0835_*`, `AC0820_S`, `AC0870_M`, `AC0882_S` erneut prüfen.
4. **Donor-Matrix einführen** und gezielt für `AC0832`, `AC0836`, `AC0882`
   gegen den bisherigen Initialisierungspfad benchmarken.

## Definition of done für den nächsten AC08-Zyklus

Ein neuer Verbesserungszyklus sollte erst als erfolgreich gelten, wenn alle
folgenden Punkte erfüllt sind:

- Die Familien `AC0811`–`AC0814` scheitern nicht mehr an Textmismatches.
- Für `_S`-Problemfälle sinkt die Zahl der `semantic_mismatch`-Abbrüche sichtbar.
- `quality_tercile_passes.csv` enthält nicht mehr fast nur
  `rejected_regression`, sondern einen klaren Anteil stabiler Verbesserungen.
- Die Anzahl erfolgreicher Template-Transfers liegt deutlich über den aktuell
  dokumentierten drei Fällen.
