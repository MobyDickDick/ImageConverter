# FALLBACK-GROUPS-CHECKER-05 – logische Geraden aus nativen Segmenten

[Umsetzung und Grenzen](../../../docs/next_arbeitspaket_2026-11-13_segment_checker.md).

Separater Freeze von `checker.py`, dem unveränderten `strict_checker.py`,
`evaluator.py` und `manifest.json`, jeweils SHA-256 in `seal.json`.
Das Manifest enthält die XML-Positiv- und Negativszenen, externe Annotationen
und die hashgebundenen historischen Entwicklungsausgaben als eingebettete Bytes.
Die Ausführung verweigert Abweichungen zwischen Quellen und Freeze.
Der vorherige Einzelprimitiv-Freeze unter `fallback_checker_v1` bleibt erhalten.

`results/summary.json`: 15 positive Szenen, 255 zurückgewiesene Gegenproben,
45 davon mit beiden Renderern rasteridentisch. Sechs historische Zielkonstruktionen
bestehen. Die 18 historischen Ausgaben besitzen passende Segmentoptionen für
das Gestänge, bleiben aber wegen drei bis sechs nicht zugeordneten Strichen
unvollständig im vorgegebenen Inventar. Keine reale Neubewertung oder Freigabe.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_segment_checker --output .tmp/segment-checker-replay
.venv/Scripts/python.exe -m pytest -q tests/test_segment_checker.py tests/test_fallback_checker.py tests/test_fallback_composition.py tests/test_fallback_groups.py tests/test_fallback_structure.py tests/test_real_composition_holdout_freeze.py
.venv/Scripts/python.exe -m tools.run_pytest_profile core-green
```

Python 3.10, `requirements-dev.txt` und `rsvg-convert` werden benötigt.
Zielordner müssen neu sein. `--freeze NEUER_ORDNER` erstellt einen neuen
Entwicklungsfreeze und überschreibt keinen vorhandenen Stand.

Vertrag: `tools.check_segment_scene.check_scene(svg, annotation)` mit
`independent_segment_scene_v1`. Teilungen müssen ausdrücklich pro Objekt
erlaubt sein. Die Prüfung verbraucht jeden nativen SVG-Bestandteil genau einmal.
Überdeckung benötigt benannte, tatsächlich zugeordnete deckende Kreise oder
Rechtecke in nachgewiesener Vordergrundposition. Ausgelassene verdeckte
Zwischenstücke bleiben ausdrücklich `hidden_geometry_verified=false`;
sie werden nicht aus den sichtbaren Segmenten als vorhandene Geometrie erfunden.
Ein positiver Entscheid bestätigt den annotierten Darstellungsvertrag.

Eine Konstruktion, fünf Transformationen und drei Darstellungen sind keine
15 unabhängigen Familien. Keine Runtimeänderung, keine neue CLI-Konvertierung,
keine Archivpromotion und null Reserveversuche. Alle realen Reserven bleiben
`sealed_unrun`; Kurvenprüfer, menschlicher Annotationsaudit und unabhängige reale
Vollständigkeitsprüfung fehlen weiterhin.
