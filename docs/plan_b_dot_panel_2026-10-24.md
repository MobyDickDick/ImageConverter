# Plan B: Rahmenregistrierung mit Subpixel-Neustart

Der gemeldete [CI-Fehler #2050](https://github.com/MobyDickDick/ImageConverter/issues/2050)
ist mit Seed `113996966622973259`, identischen Quellen-/Beschreibungs-/Rasterhashes,
64 Iterationen und 60 Sekunden Prozesslimit reproduziert: **16/17**, Exit 1.
`probe_07` erreicht IoU `0.8445040214477212`, gefordert sind unverändert `0.85`.

Die grobe erste Koordinatenbewegung verschiebt den teilweise abgeschnittenen
Rahmen nach links aus dem Bild. Die anschließende Feinregistrierung bleibt in
diesem lokalen Minimum; insbesondere fehlen 50 Vordergrundpixel der linken
Rahmenkante. Feinere Endschritte allein verbessern den RGB-Fehler, verfehlen
aber mit IoU `0.843501` weiterhin die Abnahme. Eine Auswahl nur anhand des
Registrierungsverlusts statt des Konturscores bleibt ebenfalls bei `0.844504`.

Ein zusätzlicher, begrenzter Durchlauf beginnt wieder bei den gemessenen
Rasterparametern, mit Schritten `0.5, 0.25, 0.125`. Er verwendet denselben
nativen Rahmen-/Verlaufs-/Linien-/Kreisaufbau, dieselbe Verlustfunktion und
dieselbe abschließende Kandidatenauswahl. Es gibt keine Fallkennung oder
Referenzgeometrie im Konverter. Der bestehende Cache vermeidet Doppelrenderings.
Die Suchläufe protokollieren Prüfzahl und besten Verlust.

Auf denselben 17 unveränderten CLI-Eingaben bestehen danach **17/17**, Exit 0.
Der Problemfall erreicht IoU `0.9838274932614556`; RGB-MSE sinkt von
`0.001106904` auf `0.000274248`. Die direkte Registrierung benötigt dafür
1.882 statt 1.287 Renderprüfungen. Der zusätzliche Suchaufwand ist eine
bewusste Laufzeitgrenze dieser Korrektur. Lokale parallele CLI-Laufzeiten
sind in der Evidenz enthalten und kein kontrollierter Geschwindigkeitsvergleich.

Das gesamte betroffene Runtime-Testmodul besteht **85/85**, Exit 0,
einschließlich unabhängiger Größen-/Lage-/Punktradiusprüfungen und früherer
Regressionen. Die gezielte Teilmenge besteht 8/8; die Zahlen überschneiden sich.
Ein eigener CI-Job wiederholt diese Teilmenge und den exakten 17er-CLI-Lauf.
Die zufällige Plan-B-Abnahme und sämtliche Qualitätsgrenzen bleiben erhalten.

Kompakte Messwerte, Hashes, Hypothesen und Testbefehle:
[`dot_panel_subpixel_restart_v1`](../artifacts/evaluation/dot_panel_subpixel_restart_v1/summary.json).
Die vollständigen lokalen Debug-Bäume liegen unter `.tmp/ar0030-before` und
`.tmp/ar0030-after`. Python lokal: 3.10.11. Eine vollständige Katalog- oder
Standardsuite wird mit diesem Nachweis nicht beansprucht.

Branch: `codex/plan-b-dot-registration-2026-10-24`.

## Sitzungslog

- Getestet: identischer CLI-Vorher-/Nachherlauf und betroffenes Runtime-Testmodul.
- Ergebnis: 16/17 → 17/17; 85 Tests bestanden.
- Blocker: keine für diesen Fehler; allgemeine Katalogabnahme bleibt offen.
- Nächster Schritt: separater P0-Branch für beobachtete Kreisränder bei gleicher Füllfarbe.
- Startbefehl: siehe `checks.json`, Beschreibung aus der Katalog-XML als UTF-8-Datei speichern.
