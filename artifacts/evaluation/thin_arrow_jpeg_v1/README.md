# Dünne JPEG-Pfeilschäfte: AC0020_L

Die echte CLI reproduziert mit Seed 42 den Rückfall auf die alte, gemeinsam
normalisierte Pfeilgeometrie. Der neue native Fit wird trotz sehr kleinem
Pixelfehler verworfen: Gleich helle Nachbarpixel der dünnen Schäfte erzeugen
andere Canny-Kanten als das leicht asymmetrische JPEG. Die Konturdeckung des
isolierten Fits beträgt nur 0,4025 bei Vordergrund-IoU 1,0. Weitere reine
Pixelfehleroptimierung beseitigt die Diskrepanz nicht.

Die Zielfunktion berücksichtigt jetzt zusätzlich die unveränderte
Konturmetrik (`25 * (1 - edge_alignment)`). So kann die Subpixelverfeinerung
auch die beobachteten Schaftkanten erhalten. Alle Struktur-, Beschreibungs-
und Qualitätsprüfungen bleiben aktiv. Es gibt keinen Dateinamen-Sonderfall
und keinen Zugriff auf Referenz-SVGs.

## Vergleich bei unveränderten Eingabebytes und Grenzen

| AC0020_L | Vorher | Nachher |
| --- | ---: | ---: |
| Normalisierter RGB-MSE | 0,0138354 | 0,0002470 |
| Vordergrund-MSE | 0,0838714 | 0,0020142 |
| Konturdeckung | 0,4117504 | 0,9909301 |
| Vordergrund-IoU | 0,6468039 | 1,0000000 |

Der RGB-MSE sinkt um 98,2 %. MuPDF und unabhängig librsvg bestehen für alle
drei Kataloggrößen L/M/S sämtliche Raster- und Komplexitätsgrenzen. Die
Ausgaben enthalten jeweils zwei native Rechtecke und zwei Dreiecke, ohne
eingebettete Rasterdaten. `summary.json` hält Messwerte und Prüfsummen fest.
Das Erfolgsarchiv wird nicht erweitert.

Die drei neuen Runtime-Regressionen verwenden neutrale Dateinamen und
verbieten den alten Fallback. Die L-Regression schlägt mit der ursprünglichen
Zielfunktion fehl und besteht nach der Korrektur. Die gezielte Prüfung von
Pfeilen, gefüllten Symbolen und Renderern besteht 117 Tests.

Syntaxprüfung, CLI-Hilfe und die Image-ID-Hardcoding-Prüfung bestehen ebenfalls.
Der vollständige Lauf mit 5406 gesammelten Tests wurde nach Fehlern außerhalb
dieser Pfeilkorrektur beendet. Zwei separat reproduzierte Ursachen sind ein
unverändertes AC0VR2-ZL-M-Artefakt, das vom erwarteten Fixture abweicht, und
gesperrte lokale HTTP-Verbindungen (`WinError 10013`). Der beratende
Reportkonsistenzcheck meldet bei den reinen Pfeilausgaben eine leere
Kettenzusammenfassung. `checks.json` hält diese Grenzen ausdrücklich fest;
ein grüner Gesamttestlauf wird nicht behauptet.

Die gemeinsame Katalogübersicht enthält die neue L-Ausgabe mit beiden
Renderermessungen; andere Einträge behalten ausdrücklich ihre historischen
Messstände. Die vollständige Laufzeit-Neuvermessung wurde zugunsten dieser
gezielten Aktualisierung beendet. Weitere 18 Katalog-/HTML-Tests bestehen.

```powershell
.venv/Scripts/python.exe -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir .tmp/thin-arrow-replay --start AC0020_L --end AC0020_S --search-seed 42 --deterministic-order
.venv/Scripts/python.exe -m pytest -q tests/test_arrow_pair_runtime.py tests/detailtests/test_dual_arrow_runtime_helpers.py tests/detailtests/test_rendering_gradient_compatibility.py tests/test_filled_symbols_runtime.py
```

Konvertierungen zur Nachprüfung in ein neues Ausgabeverzeichnis schreiben.
Die aktuelle L-Ausgabe und ihre Messdaten sind zusätzlich als
`artifacts/converted_images/reports/conversion_bestlist_snapshots/AC0020_L.svg`
und `.json` gesichert.
