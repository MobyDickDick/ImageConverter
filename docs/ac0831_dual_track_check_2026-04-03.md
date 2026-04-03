# AC083 exemplar check (dual-track global search)

Datum: 2026-04-03

## Ziel
Exemplarisch prüfen, ob die zweigleisige Suche (stochastic + deterministic) im realen Lauf greift und ob pro Bild das bessere Ergebnis übernommen wird.

## Ausführung
Verwendeter Lauf:

```bash
PYTHONPATH=. python -m src.imageCompositeConverter artifacts/images_to_convert \
  --csv-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir /tmp/ac0831_eval_dual \
  --start AC0831 --end AC0831 --deterministic-order
```

Auswertung der erzeugten Reports (`/tmp/ac0831_eval_dual/reports/*_element_validation.log`) anhand der Logzeile
`global-search: track-vergleich (stochastic_err=..., deterministic_err=..., gewählt=...)`.

## Ergebnis je Bild

| Bild | Vergleiche | Min stochastic_err | Min deterministic_err | Ø(det-stoch) | Stoch-Wins | Det-Wins | Bester Gesamtfehler |
|---|---:|---:|---:|---:|---:|---:|---:|
| AC0831_L | 6 | 19.948 | 21.954 | +0.460 | 3 | 3 | 19.948 |
| AC0831_M | 8 | 18.044 | 18.044 | +0.532 | 7 | 1 | 18.047 |
| AC0831_S | 6 | 21.424 | 21.424 | +0.339 | 4 | 2 | 21.424 |

## Kurzfazit
- Die Track-Vergleichszeilen werden im Lauf geschrieben; damit ist bestätigt, dass beide Verfahren in der Praxis ausgeführt und verglichen werden.
- In diesem exemplarischen AC0831-Subset gewinnt stochastisch häufiger, der deterministische Track liefert aber ebenfalls in mehreren Runden den Gewinner.
- Das Übernahmekriterium „besserer Track gewinnt“ funktioniert sichtbar pro Runde.
