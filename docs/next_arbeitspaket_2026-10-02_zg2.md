# Nächstes Arbeitspaket – ZG2 Runtime-Sonderfall-Abschluss (2026-10-02)

Dieses Paket arbeitet die erste noch offene Leitaufgabe aus
`docs/open_tasks.md` ab: **ZG2 – Bildspezifische Logik aus Hauptpfad
entfernen**. Die dafür notwendige Migration wurde in den später ergänzten
IDO-P2-/IDO-P3-Paketen bereits technisch umgesetzt, war im älteren ZG-Abschnitt
aber noch nicht als abgeschlossen nachgezogen.

## Inventur und Abschlussbeleg

- `tools/check_no_new_image_id_hardcoding.py` scannt alle Python-Dateien unter
  `src/` und verbietet Katalogkennungen der Familien `AC`, `AR`, `GE`, `DLG`
  und `SE` ohne Allowlist oder Legacy-Baseline.
- Die aktuelle Nullprüfung meldet `0` Runtime-ID-Vorkommen. Damit kann der
  Hauptpfad keine Auswahl mehr direkt an eine bekannte Katalog-ID koppeln.
- Die Filename-Invarianztests führen identische Pixel und Beschreibungen unter
  katalogfremden Zufallsnamen durch und vergleichen normalisierte Geometry-IR-
  und SVG-Ergebnisse.
- Die End-to-End-Holdout-Abnahme prüft zusätzlich umbenannte Referenzfälle und
  weist weder ursprüngliche Namen noch Katalogtokens in den Runtime-Zeilen aus.

## Revalidierung

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 \
  python tools/check_no_new_image_id_hardcoding.py
```

Ergebnis: `PASS: no image-ID hardcoding found in runtime source code (0 occurrences).`

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 \
  python -m pytest -q \
  tests/test_no_new_image_id_hardcoding.py \
  tests/detailtests/test_filename_invariance.py \
  tests/test_end_to_end_holdout_acceptance.py
```

Ergebnis: `7 passed`.

## Ergebnis und nächster Schritt

ZG2 ist abgeschlossen: Der Runtime-Hauptpfad enthält keine katalogspezifischen
IDs, und das Referenzset bestätigt gleiches fachliches Verhalten nach einer
Umbenennung. Die nächste offene Leitaufgabe ist **ZG3 – Good-Solution-Gate v1**.
