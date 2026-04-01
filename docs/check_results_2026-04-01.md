# Verifikationslauf 2026-04-01

## Geprüfte Befehle

1. `python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0881 --end AC0881`
2. `python -m pytest -q`

## Ergebnis: Aufruf für AC0881

Der Aufruf bricht direkt beim Import mit einem `NameError` ab:

- Datei: `src/iccFs/optionalDependencyBaseDir.py`
- Fehler: `optional_dependency_base_dir = optionalDependencyBaseDir`
- Problem: `optionalDependencyBaseDir` ist nicht definiert.

## Ergebnis: Testlauf

`pytest` bricht bereits in der Test-Collection mit 3 Fehlern ab:

1. `NameError` in `src/iccFs/optionalDependencyBaseDir.py` (`optionalDependencyBaseDir` nicht definiert).
2. Derselbe `NameError` erneut über weiteren Importpfad.
3. `NameError` in `src/iccFs/mF/overviewTiles.py` (`readRaster = readRaster`, aber `readRaster` ist nicht definiert).

## Fazit

- Der angefragte AC0881-Aufruf funktioniert aktuell **nicht**.
- Die Testsuite funktioniert aktuell **nicht** (Abbruch in Collection).
