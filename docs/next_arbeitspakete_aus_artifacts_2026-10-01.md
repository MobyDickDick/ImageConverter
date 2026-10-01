# Nächste Arbeitspakete aus den hochgeladenen Artefakten (2026-10-01)

## Kurzfazit

Die hochgeladenen Daten bilden **noch keinen abgeschlossenen Kataloglauf** ab.
Der belastbarste nächste Schritt ist daher nicht weiteres Pixel-Feintuning an
historischen Spitzenreitern, sondern zuerst die Fortsetzung und Konsolidierung
des unterbrochenen Laufs. Der Checkpoint steht bei Variantenindex `87`
(`AC0212_S.jpg`), enthält `84` verarbeitete Resultate und vier semantische
Fehler. Die zugehörige Result-Map enthält 85 Einträge. Gleichzeitig enthält die
Bestenliste 562 Zeilen und die Pixel-Zusammenfassung spricht von 566 Bildern.
Diese unterschiedlichen Bezugsräume dürfen nicht zu einer gemeinsamen
Erfolgsquote vermischt werden.

Aus diesem Befund werden fünf priorisierte, voneinander abgrenzbare
Arbeitspakete abgeleitet. **AP0 ist Voraussetzung für AP3 und AP4.** AP1 und AP2
können nach einem reproduzierbaren Snapshot parallel fachlich bearbeitet
werden.

## Verwendete Evidenz und Grenzen der Aussage

| Evidenz | Beobachtung | Konsequenz |
| --- | --- | --- |
| `conversion_checkpoint.json` | `stage=initial_pass`, letzter Event `AC0212_S.jpg`, Index 87, 84 verarbeitete Resultate, 4 Fehler | Der Lauf ist fortzusetzen, nicht als abgeschlossen zu bewerten. |
| `conversion_result_map.json` | 85 Resultate; höchster aktueller `mean_delta2` u. a. bei `AC5040_L`, `GE0281`, `GE1420_L` | Nur als **vorläufige** Qualitätswarteschlange verwenden. |
| `batch_failure_summary.csv` | Vier `semantic_mismatch`: drei fehlende Kreisdetektionen, ein Beschreibungs-/Bildkonflikt | Zwei verschiedene Fehlerklassen statt eines Sammelfixes. |
| `optimization_render_telemetry_summary.json` | 83 Konvertierungen, keine Renderfehler und keine Render-Timeouts | Der aktuelle Engpass ist nicht der Renderer; AP1/AP2 priorisieren. |
| `quality_tercile_passes.csv` | Zwei DLG0021-Nachläufe ohne Verbesserung, beide wegen räumlicher Regression verworfen | DLG0021 nicht erneut mit bloß höherem Budget starten. |
| `cross_family_hypothesis_metrics.csv` | Beide globalen AC08-Hypothesen sind `rejected` | Keine pauschale AC08-Geometrieübertragung implementieren. |
| `chain_phase_telemetry_summary.txt` | `conversion_count=0`, obwohl Result-Map und Optimierungs-Telemetrie Resultate enthalten | Zusammenfassung ist leer/stale oder stammt aus einem anderen Lauf. |

Die historische `conversion_bestlist.csv` bleibt als Vergleichs- und
Regressionsbasis wertvoll, ist aber wegen ihres größeren Umfangs kein Beleg
für die Vollständigkeit des aktuellen Checkpoint-Laufs.

## AP0 – Unterbrochenen Kataloglauf reproduzierbar fortsetzen und abschließen

**Priorität:** P0  
**Ziel:** Einen konsistenten, wiederaufnehmbaren Lauf mit eindeutigem Run-Bezug
erzeugen, bevor neue globale Qualitätsaussagen getroffen werden.

### Umfang

1. Den Lauf mit dem im Checkpoint dokumentierten `run_seed=529189183`, dem
   vorhandenen Result-Map-Pfad und der vorgesehenen Resume-Funktion fortsetzen.
2. Vor dem Resume einen unveränderlichen Snapshot von Checkpoint, Result-Map,
   Fehlerliste und Telemetrie ablegen.
3. Nach jedem verarbeiteten Bild atomar sicherstellen, dass Checkpoint-Zähler,
   Result-Map und Fehlerliste denselben Fortschritt abbilden.
4. Beim Abschluss eine Run-ID und einen gemeinsamen Nenner in alle aggregierten
   Reports schreiben; historische Bestenliste getrennt kennzeichnen.

### Akzeptanzkriterien

- Ein Abbruch und anschließendes Resume verarbeitet kein bereits bestätigtes
  Bild doppelt und verliert kein Resultat.
- `processed_result_count`, die Anzahl der Result-Map-Einträge und die Anzahl
  erfolgreicher plus fehlgeschlagener Resultate sind erklärbar; eine zulässige
  Abweichung (z. B. „aktuelles Bild bereits geschrieben, Checkpoint noch nicht“)
  ist explizit dokumentiert und nach dem Abschluss null.
- Ein Abschlussmanifest enthält Run-ID, Seed, Start-/Endzeit, Eingangsmenge,
  Erfolg, fachliche Fehler, technische Fehler und Timeouts.
- Der Abschlussreport darf erst dann als Katalogquote bezeichnet werden, wenn
  `stage=complete` gesetzt ist.

## AP1 – Kreisdetektion bei kleinen Anschluss-/Symbolvarianten stabilisieren

**Priorität:** P1  
**Betroffene Evidenz:** `AC0704_1_S`, `AC0714_M`, `AC0703_1_M`  
**Ziel:** Falsche semantische Ablehnungen durch eine robuste, skalierte
Kreis-/Ring-Evidenz reduzieren, ohne das Gate pauschal abzuschalten.

### Umfang

1. Die drei Rohbilder samt Beschreibung und `*_failed.svg` als feste
   Repro-Fixtures sichern.
2. Hough-, Kontur- und Maskenbefunde je Fixture getrennt protokollieren
   (Radiusbereich relativ zur Canvas, Kontrast, Randkontakt, Confidence).
3. Einen kombinierten Kreis-/Ringentscheid mit größenrelativen Grenzwerten
   entwickeln; bei widersprüchlicher Evidenz `needs_review` statt eines
   vorgetäuschten `semantic_ok` liefern.
4. Negative Kontrollbilder ohne Kreis in die Regression aufnehmen.

### Akzeptanzkriterien

- Alle drei positiven Fixtures liefern reproduzierbar einen belastbaren Kreis-
  oder Ringkandidaten oder eine fachlich begründete `needs_review`-Entscheidung.
- Die Negativ-Fixtures bleiben negativ; keine generelle Lockerung des
  Semantik-Gates.
- Der Report nennt Detektorquelle, Geometrie, Confidence und
  Ablehnungsgrund maschinenlesbar.
- Bestehende AC08-Kreis-/Ringtests bleiben grün.

## AP2 – Bild-/Beschreibungs-Konflikt für `AC0843_L` klären

**Priorität:** P1  
**Ziel:** Den erkannten senkrechten Strich entweder fachlich in der Beschreibung
abbilden oder als Detektionsartefakt widerlegen; keine ID-spezifische
Renderer-Ausnahme einführen.

### Umfang

1. Rohbild, Beschreibung, Detektionsregionen und Failed-SVG gemeinsam in einem
   kleinen Evidence-Sheet darstellen.
2. Prüfen, ob der Strich eigenständiges Primitive, Kellenstiel, Kreisrand oder
   JPEG-/Antialiasing-Artefakt ist.
3. Bei fachlich echtem Primitive die Quelldatenbeschreibung korrigieren und den
   allgemeinen Description-Contract erneut ausführen. Andernfalls die
   Linienklassifikation anhand geometrischer Evidenz korrigieren.
4. Die Entscheidung als Datenkorrektur oder Detektorfix markieren, damit sie
   nicht stillschweigend in eine Bild-ID-Regel wandert.

### Akzeptanzkriterien

- Die Ursache ist mit Overlay und messbaren Detektionsdaten belegt.
- `AC0843_L` durchläuft danach den normalen semantischen Pfad oder endet
  nachvollziehbar in `needs_review`.
- Mindestens zwei verwandte AC0843-/Kellenvarianten sichern die
  Generalisierung ab.

## AP3 – Vorläufige Qualitätswarteschlange nach abgeschlossenem Lauf neu bilden

**Priorität:** P2, abhängig von AP0  
**Ziel:** Die schwächsten technisch erfolgreichen Konvertierungen anhand
vergleichbarer aktueller Metriken auswählen, statt historische und partielle
Reports zu vermischen.

### Startkandidaten aus der partiellen Result-Map

1. `AC5040_L` (`mean_delta2=18220.181641`)
2. `GE0281` (`mean_delta2=15287.335938`)
3. `GE1420_L` (`mean_delta2=13038.978516`)
4. `GE9011_2M` (`mean_delta2=12552.657227`)
5. `GE9012_7M` (`mean_delta2=12271.906250`)

Diese Reihenfolge ist ausdrücklich nur eine Startwarteschlange. Nach AP0 wird
sie aus dem vollständigen aktuellen Lauf neu berechnet und zusätzlich nach
`spatial_quality_score`, strukturierter Fehlerverteilung, Bildfläche und
Familienabdeckung triagiert.

### Akzeptanzkriterien

- Die Auswahl stammt ausschließlich aus derselben abgeschlossenen Run-ID.
- Semantische Fehler werden nicht als Pixel-Optimierungsfälle einsortiert.
- Pro Kandidat existieren Vorherbild, SVG, Diff, Metriken, Erzeugungspfad und
  eine Hypothese zum dominanten Restfehler.
- Maximal fünf aktive Kandidaten; ein Kandidat rückt erst nach dokumentiertem
  Abschluss oder Blocker nach.
- DLG0021 wird nur mit einer neuen strukturellen Hypothese erneut eingeplant,
  nicht mit einer weiteren bloßen Budgeterhöhung.

## AP4 – Report-Konsistenzgate und Lauf-Provenienz einführen

**Priorität:** P2, abhängig von AP0  
**Ziel:** Leere oder veraltete Summaries sowie vermischte Run-Umfänge vor einer
fachlichen Auswertung automatisch erkennen.

### Umfang

1. Kleines Prüftool für JSON/CSV/TXT-Reports erstellen.
2. Pflichtfelder `schema_version`, `run_id`, `generated_at`, `input_count`,
   `processed_count` und `source_report` für neue Summaries definieren.
3. Invarianten prüfen: Zählergleichheit, bekannte Statuswerte, referenzierte
   Logdateien vorhanden, keine doppelten Dateinamen und keine Summary mit null
   Konvertierungen bei nichtleerer Result-Map derselben Run-ID.
4. Das Gate in den lokalen Abschlusscheck integrieren und bei unvollständigem
   Lauf einen klaren Warnstatus statt falschem `pass` ausgeben.

### Akzeptanzkriterien

- Der aktuelle Widerspruch zwischen `chain_phase_telemetry_summary.txt`
  (`conversion_count=0`) und den anderen aktuellen Resultaten wird erkannt.
- Das Tool unterscheidet `complete`, `incomplete`, `stale/mixed-run` und
  `invalid` und beendet sich bei `stale/mixed-run` oder `invalid` ungleich null.
- Fixture-Tests decken den aktuellen partiellen Snapshot sowie einen
  konsistenten abgeschlossenen Beispielsnapshot ab.

## Empfohlene Reihenfolge

1. **AP0** – Snapshot, Resume, Abschlussmanifest.
2. **AP1 und AP2** – die vier fachlichen Fehler nach Ursachenklasse bearbeiten.
3. **AP4** – die beim Abschluss sichtbar gewordenen Konsistenzregeln
   automatisieren.
4. **AP3** – erst auf der danach konsistenten Vollmenge die nächsten maximal
   fünf Qualitätskandidaten festlegen.

Damit wird aus den Artefakten ein belastbarer Arbeitsfluss: zuerst
Vollständigkeit und Provenienz, dann Semantikfehler, danach gezielte
Qualitätsoptimierung.
