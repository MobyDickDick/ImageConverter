# Nächstes Arbeitspaket – T6.2 AC0837-L-Isolation Run PL (2026-06-14)

## Ziel

Run PL schließt den nächsten sehr hoch priorisierten Langläufer nach T6.1:
`AC0837_L` muss im bestehenden AC08-Regressionstest real konvertiert werden,
den semantischen Status `semantic_ok` behalten und isoliert innerhalb von
120 Sekunden abschließen.

## Ursache des bisherigen Skips

Der parametrisierte Regressionstest enthielt für `AC0837_L` einen festen Skip,
weil der historische Einzellauf `198.28s` benötigte. Dadurch war die NodeID zwar
in der Suite sichtbar, prüfte aber weder die SVG-Ausgabe noch den semantischen
Status.

## Umsetzung

- Der feste `AC0837_L`-Skip wurde entfernt.
- Die Variante wird mit ihrem Rasterbild und der XML-Beschreibung in ein
  temporäres Einvarianten-Eingabeverzeichnis kopiert.
- `convertRange(...)` verarbeitet ausschließlich `AC0837_L`, deterministisch
  und mit zwei Iterationen.
- Der AC0837-Validierungspfad erhält innerhalb genau dieses Regressionstests
  ein 60-Sekunden-Budget. Produktionsläufe und andere Varianten behalten ihre
  bisherigen Budgets.
- Der Test prüft weiterhin ein reguläres SVG, das Fehlen eines
  `AC0837_L_failed.svg` und `status=semantic_ok` im Elementvalidierungslog.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 120 env PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest -q \
'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok]'
```

| Kriterium | Gefordert | Run PL |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=120s` | `113.07s` |
| Wandzeit | `<=120s` | `113.869s` |
| `AC0837_L.svg` | vorhanden | vorhanden |
| `AC0837_L_failed.svg` | nicht vorhanden | nicht vorhanden |
| Semantischer Status | `semantic_ok` | `semantic_ok` |

Gegenüber der historischen Laufzeit von `198.28s` sinkt die Pytest-Dauer um
rund `42.98 %`.

## 5-Zeilen-Log

- **Getestet:** Reale isolierte AC0837-L-Konvertierung über die bisher übersprungene Regressionstest-NodeID.
- **Ergebnis:** Exit `0`, `1 passed in 113.07s`, reguläres SVG und `status=semantic_ok`.
- **Blocker:** Kein Blocker für T6.2; das 120-Sekunden-Akzeptanzziel ist erfüllt.
- **Nächster Schritt:** T6.3 (`AC0838_M`) als nächsten sehr hoch priorisierten Langläufer unter das 90-Sekunden-Ziel bringen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout`.
