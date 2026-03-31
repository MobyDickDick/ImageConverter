# Analyse: Checkout-Probleme durch lange Pfade & polnische Notation

Datum: 2026-03-31

## Kurzfazit

- Das Problem ist reproduzierbar durch sehr tiefe Modulpfade unter `src/imageCompositeConverterFs/mainFiles/...`.
- Es gibt **mindestens 1 Datei mit simuliertem Windows-Pfad > 260 Zeichen** (bei Basis `C:/work/ImageConverter/...` sogar 265 Zeichen).
- Die aktuelle "Files"-Namenskonvention ist fast überall konsistent, aber bei **6 Ordnern fehlt der führende `_`-Präfix** (wenn wir polnische Notation als `_verb_objektFiles` interpretieren).

## Gemessene längste Pfade

Top 5 (Windows-Simulation `C:/work/ImageConverter`):

1. `src/imageCompositeConverterFs/mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_restore_successful_conversion_snapshotFiles/_successful_conversion_snapshot_pathsFiles/_successful_conversion_snapshot_dir.py` → 265
2. `src/imageCompositeConverterFs/mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_store_successful_conversion_snapshotFiles/_successful_conversion_snapshot_pathsFiles/_successful_conversion_snapshot_dir.py` → 263
3. `src/imageCompositeConverterFs/mainFiles/convert_rangeFiles/_in_requested_rangeFiles/_matches_partial_range_tokenFiles/_shared_partial_range_tokenFiles/_compact_range_tokenFiles/_normalize_range_tokenFiles/get_base_name_from_file.py` → 254
4. `src/imageCompositeConverterFs/mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_read_successful_conversion_manifest_metricsFiles/_parse_successful_conversion_manifest_line.py` → 234
5. `src/imageCompositeConverterFs/mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/_format_successful_conversion_manifest_lineFiles/_successful_conversion_metrics_available.py` → 231

## Polnische Notation bei Ordnernamen

Wenn wir für ausgelagerte Modulordner den Stil `_aktion_objektFiles` ansetzen, sind diese Ordner noch inkonsistent:

- `src/imageCompositeConverterFs/mainFiles`
- `src/imageCompositeConverterFs/mainFiles/convert_rangeFiles`
- `src/imageCompositeConverterFs/mainFiles/export_module_call_tree_csvFiles`
- `src/imageCompositeConverterFs/mainFiles/build_linux_vendor_install_commandFiles`
- `src/imageCompositeConverterFs/mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles`
- `src/imageCompositeConverterFs/mainFiles/convert_rangeFiles/update_successful_conversions_manifest_with_metricsFiles/collect_successful_conversion_quality_metricsFiles`

## Vorschlag zur Kürzung (ohne Funktionsverlust)

1. **Sofortmaßnahme für Windows-Checkout**
   - Lokal `git config core.longpaths true` aktivieren.
   - Repository in einen sehr kurzen Basispfad klonen (z. B. `C:\w\ic`).

2. **Strukturelle Kürzung im Repo (empfohlen)**
   - Lange Tokens abkürzen (z. B. `successful` → `succ`, `conversion` → `conv`, `manifest` → `man`, `metrics` → `met`, `snapshot` → `snap`).
   - Besonders tiefe Segmente zuerst umbenennen (`update_successful_conversions_manifest_with_metricsFiles` etc.).

3. **Konventionsharmonisierung für Ordnernamen**
   - Fehlende `_`-Präfixe ergänzen, damit Dateien und Ordner dieselbe polnische Notation verwenden.
   - Beispiel: `mainFiles` → `_mainFiles`, `convert_rangeFiles` → `_convert_rangeFiles`.

## Nächster Schritt

Wenn gewünscht, kann ich in einem zweiten Schritt eine **sichere Rename-Migration** vorbereiten (inkl. Import-/Loader-Anpassung und automatischem Check), damit die langen Pfade dauerhaft unter der Windows-Grenze bleiben.
