# CONVERSION-PERSISTENCE-01: lokale Abnahme vom 12.11.2026

Umfang und Grenzen:
[Arbeitspaket](../../../docs/next_arbeitspaket_2026-11-12_conversion_persistence.md).
Maschinenlesbare Befehle, JUnit-Zähler und aktuelle Dateiidentitäten:
[summary.json](summary.json).

- 160/160 gezielte Regressionen: darunter Schreibfehler bei der Veröffentlichung,
  konsistente alte Checkpoints, unveränderliche frühere Läufe, Legacy-Sicherung,
  beschädigte Index-/Ergebnis-/SVG-Objekte, geänderte Originale/Beschreibungen,
  exakte Wiederherstellung von Windows-Zeilenenden, deduplizierte große
  Suchhistorien, beide Bilddurchläufe und Abbrüche am öffentlichen Bereichseinstieg.
- 28/28 Prozessaufsichts-/Timingprüfungen: unter anderem echte Prozessstarts,
  Deadline-/Abbruchbehandlung und zwei Produktions-CLI-Konvertierungen im selben
  Ausgabeordner. Der zweite Aufruf lässt sämtliche Dateien des ersten Laufordners
  bytegleich; der aktuelle Checkpoint verweist auf ein hashgebundenes bestätigtes
  Ergebnis. Die Elternaufsicht rendert weiterhin nicht.
- 42/42 `core-green`-Tests. Keine übersprungenen Tests in diesen drei Läufen.
  Die Gruppen überschneiden sich; ihre Zähler sind keine unabhängigen Stichproben.
- `compileall`, `git diff --check` und das Gate gegen neue Bild-ID-Weichen bestanden.

Die JUnit-Rohprotokolle liegen lokal unter
`.tmp/conversion-persistence-{targeted,integration,core}.xml`. Die Tests räumen
ihre erzeugten Konvertierungen anschließend auf; die dauerhaft aufbewahrte
Abnahme besteht aus den reproduzierbaren Tests und der kompakten Zusammenfassung.

Kurze Wiederholung:

```powershell
python -m pytest -q tests/test_conversion_persistence.py
python -m pytest -q tests/test_conversion_deadline.py tests/test_conversion_timing.py
python tools/run_pytest_profile.py core-green
python tools/check_no_new_image_id_hardcoding.py
git diff --check
```

Die vollständige Auswahl der 160 gezielten Tests steht als Argumentliste in
`summary.json`. Der neue CI-Job `conversion-persistence` prüft Windows und Ubuntu;
sein erster GitHub-Lauf ist noch nicht Bestandteil dieses lokalen Nachweises.
Keine vollständige Katalog-, neue Formen-/Familien- oder Stromausfallabnahme.
