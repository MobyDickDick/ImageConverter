# Einzelne JPG→SVG Probe ohne Embedded-JPG (Run ET2, 2026-05-16)

## Ziel
Prüfen, ob ein einzelnes JPG aktuell in ein SVG konvertiert werden kann, **ohne** ein eingebettetes JPG (`<image ...>`) im Ergebnis.

## Ausführung
1. Konvertierung (isoliert auf `AC0812`):
   - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic_test/a/b/c --start AC0812 --end AC0812 --deterministic-order`
2. Embedded-Check auf den erzeugten SVGs:
   - `rg -n "<image|xlink:href|href=\"data:image" /tmp/ic_test/a/b/c/converted_svgs/AC0812_{L,M,S}.svg`

## Ergebnis
- `AC0812_L.svg`: kein `<image`-Treffer
- `AC0812_M.svg`: kein `<image`-Treffer
- `AC0812_S.svg`: kein `<image`-Treffer

Damit liegt ein reproduzierbarer Nachweis vor, dass mindestens dieser Einzelpfad derzeit SVGs ohne eingebettetes JPG erzeugt.

## Hinweis zu Bildbeschreibungen
Für diesen konkreten Pfad (`AC0812`) waren keine neuen Bildbeschreibungen nötig, da eine passende Beschreibung bereits in `Finale_Wurzelformen_V3.xml` vorhanden ist.
