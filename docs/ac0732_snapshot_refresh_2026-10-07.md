# AC0732_1_S: konsistente SVG-Referenz und Qualitätsprüfung

Der fehlgeschlagene Review-Test renderte die aktuelle Katalogausgabe,
verglich sie aber mit dem Messwert eines anderen SVGs im Bestenlisten-Snapshot.
Die aktuelle Ausgabe enthielt bereits Quadrat, linken Anschluss und horizontales
„P“ (`mean_delta2=3652.298584`). Der alte Snapshot enthielt stattdessen eine
gedrehte Kreisscheibe ohne Anschluss und Beschriftung (`11705.263672`).
Eine Änderung des Test-Fallbacks hätte nichts behoben: Bei vorhandenem
Snapshot-Messwert wird dieser Fallback nicht verwendet.

Ein frischer CLI-Lauf mit Original-JPEG, unveränderter XML-Beschreibung,
Seed 0, deaktivierter Ausgabevariation und `semantic-only` erzeugt die
beschriebene Vektorstruktur mit `mean_delta2=3584.535889`. Ein zweiter,
isolierter Lauf reproduziert die SVG-Bytes exakt. Aktualisiert wurden SVG,
PNG, Differenzbilder, Validierungslog, Snapshot einschließlich Metadaten
und ausschließlich die betreffende Zeile der gemeinsamen Ergebnisberichte.
Der produktive Bestenlisten-Erhaltungsschutz akzeptiert die neue Ausgabe:
Der Raumscore verbessert sich gegenüber der bisherigen Katalogausgabe von
`13346.329682` auf `13186.363828`. Der separate Optimierungsfehler steigt dabei
leicht von `14.267556` auf `14.379556`; die vollständigen Werte stehen im Report.

Die drei Review-Tests für S, M und L rendern jetzt ausdrücklich das SVG
aus demselben Snapshot-Verzeichnis wie ihre erwarteten Messwerte. Der S-Test
verlangt zusätzlich Quadrat, Anschluss und „P“, verbietet Kreisersatz und
Raster-Embedding und behält die ursprüngliche, vom Snapshot unabhängige
Obergrenze `3659.341309` bei. Ein schlechterer Snapshot kann den Test damit
nicht allein durch einen aktualisierten Erwartungswert grün machen.

Die Konvertierungslogik wurde hier nicht geändert. Die lokale Fehlerverteilung
des kleinen Symbols bleibt `structured`; die Bildqualität ist damit weiterhin
ein Kandidat für eine spätere Verbesserung und wird nicht als vollständiger
Qualitätspass ausgegeben.

Belege stehen unter
`artifacts/evaluation/ac0732_snapshot_refresh_2026-10-07/`: Vorher-/Nachher-SVGs,
Messwerte und Quellhashes in `report.json`, CLI-Logs und `reproduce.py` für einen
erneuten isolierten Lauf. Die verwendete Umgebung ist CPython 3.12.14,
NumPy 2.5.3, OpenCV 4.14.0, PyMuPDF 1.26.7.

Der Abschluss umfasst `compileall src tests`, die vollständige Default-Testsuite,
CLI-Help-Smoke und Runtime-ID-Nullprüfung. Das Ergebnis steht in `completion.json`
und `pytest.log` im Belegordner. Für temporäre Pytest-Dateien wird unter Windows
ein frisches `--basetemp` im Workspace verwendet; ein anfänglicher Lauf mit dem
nicht zugänglichen Standard-Tempverzeichnis wurde abgebrochen und getrennt
protokolliert.

Abschluss: **1628 passed, 29 skipped**, keine fehlgeschlagenen Tests.
Syntaxprüfung, CLI-Help und Runtime-ID-Nullprüfung sind grün.
