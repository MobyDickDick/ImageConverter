# Nächstes Arbeitspaket – ZG7.5 Baseline und hartes Zufriedenheitsgate (2026-10-03)

Dieses Paket setzt nach ZG7.4 den fünften Schritt der dokumentierten Folge
`ZG7.1 → ZG7.2 → ZG7.3 → ZG7.4 → ZG7.5 → ZG7.6` um. Eine technische
Beendigung, eine Verbesserung gegenüber der Baseline und ein
zufriedenstellendes Ergebnis sind nun drei unabhängige Reportfelder.

## Versiegelte Baseline

`config/semantic_only_zg7_baseline_v1.json` fixiert den ersten vollständigen
ZG7.4-Lauf mit Commit, Seed, Python-/Optimiererversion sowie den Bild- und
Beschreibungs-Hashes aller drei Fälle. `baseline_sha256` versiegelt den
kanonischen Inhalt; eine nachträgliche Änderung wird vom Evaluator abgelehnt.
Die Ausgangsmetriken sind die deterministische Qualitätsprojektion der
ZG7.4-Initialverluste. Das Kandidaten-Fixture enthält entsprechend die
Endverluste und die daraus erzeugten, rein vektoriellen Ergebnis-SVGs.

## Doppeltes hartes Gate

`tools/evaluate_satisfaction_gate.py` klassifiziert jede Metrik als
`improved`, `unchanged` oder `regressed`. Ein Fall erhält
`satisfactory=true` ausschließlich, wenn er technisch beendet ist, keine
Metrik regressiert, das Good-Solution-Gate besteht und zusätzlich das
Quality-Complexity-Gate besteht. Unabhängige harte Ablehnungsgründe schützen
insbesondere gegen eingebettete Raster und falsche SVG-Dimensionen; ein
semantisch falsches, pixelnahes Ergebnis scheitert an beiden Qualitätsgates.

## Abnahme

Der maschinenlesbare Beleg unter
`artifacts/evaluation/semantic_only_satisfaction_report_v1/report_2026-10-03.json`
weist drei technisch beendete, zwei verbesserte und drei zufriedenstellende
Fälle aus. Der unveränderte Polygonfall bleibt ausdrücklich
`improved=false`, obwohl er beide Qualitätsgates besteht. Tests belegen zudem,
dass jede Regression, ein Raster-Embed, falsche Dimensionen und eine
semantische Regression die Zufriedenheitsentscheidung hart sperren. Derselbe
Baseline-/Kandidatenaufruf erzeugt byteidentische Entscheidungen:

```bash
python tools/evaluate_satisfaction_gate.py \
  config/semantic_only_zg7_baseline_v1.json \
  config/semantic_only_zg7_candidate_v1.json \
  --output /tmp/semantic_only_satisfaction_report_v1.json
```

ZG7.5 ist abgeschlossen. Das nächste dokumentierte Paket ist **ZG7.6 –
Plan-B-Pilot ohne Sonderwissen**.
