# Wiederholungsprüfung AC0010/AC0100 (2026-10-04)

## Anlass

`nextPrompt.txt` meldet erneut, dass die AC0100-Familie nur in der großen
Variante plausibel wirke und dass Basis-, M- und S-Variante nicht über fest
abgelegte Daten gelöst werden dürfen. Geprüft wurden deshalb erneut das
Basissymbol `AC0010` und die real vorhandenen Varianten `AC0100_L`,
`AC0100_M` und `AC0100_S`.

## Ergebnis

Die Regression ist auf dem aktuellen Stand weiterhin nicht reproduzierbar. Alle
vier Varianten laufen erfolgreich durch den algorithmischen Pfad
`non_composite_elementwise_symbol_fit`. Die Validierungslogs enthalten keinen
`template_transfer`-Eintrag und keinen
`non_composite_plan_b_sample_svg_selected`-Status. Damit werden die Ausgaben aus
Rasterbild und Beschreibung erzeugt; vorhandene Sample-SVGs oder frühere
Bestlisten-SVGs wurden in diesem geprüften Pfad nicht als Quelle verwendet.

| Variante | best_error | mean_delta2 | Pfad |
|---|---:|---:|---|
| AC0010 | 19.453021 | 2170.519775 | `non_composite_elementwise_symbol_fit` |
| AC0100_L | 10.531042 | 636.508728 | `non_composite_elementwise_symbol_fit` |
| AC0100_M | 11.729074 | 818.647217 | `non_composite_elementwise_symbol_fit` |
| AC0100_S | 10.767917 | 655.151245 | `non_composite_elementwise_symbol_fit` |

Alle Werte liegen innerhalb der bestehenden schweren Regressionstest-Grenzen:
`AC0010` bleibt unter `best_error < 25.0` und `mean_delta2 < 3000.0`; die
AC0100-Größenvarianten bleiben unter `best_error < 18.0`, `AC0100_L` unter
`mean_delta2 < 1800.0` sowie `AC0100_M`/`AC0100_S` unter
`mean_delta2 < 1600.0`.

## Ausgeführte Prüfung

Die lokale `.venv` ist auf diesem Rechner defekt und verweist auf einen nicht
mehr vorhandenen Python-3.10-Interpreter. Für die Verifikation wurden daher die
Testabhängigkeiten temporär isoliert installiert und der Converter-Prozess für
diesen Lauf auf diese Dependency-Quelle gelenkt, ohne die Projektlogik zu
ändern.

```text
AC0010, AC0100_L, AC0100_M und AC0100_S wurden einzeln mit
src.imageCompositeConverter.main(...) ausgeführt:

artifacts/images_to_convert
--descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml
--output-dir artifacts/tmp_ac0100_codex_check
--start <variant>
--end <variant>
--deterministic-order
```

Der temporäre Output-Ordner wurde nach der Auswertung wieder entfernt.

## Schlussfolgerung

Für die in `nextPrompt.txt` beschriebene AC0100-Aufgabe ist keine weitere
bildnamenspezifische Korrektur erforderlich. Die vorhandene allgemeine
algorithmische Korrektur bleibt wirksam; die nächste echte Folgearbeit sollte
erst ansetzen, wenn ein neuer Repro mit abweichenden Metriken oder einem
Sample-/Template-Status vorliegt.
