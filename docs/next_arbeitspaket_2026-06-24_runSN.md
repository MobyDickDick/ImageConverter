# Nächstes Arbeitspaket – DLG0016 Dual-Arrow-Batchfehler Run SN (2026-06-24)

Run SN arbeitet die automatisch erzeugte Folgeaufgabe aus `docs/open_tasks.md` ab: **Fehleranalyse `DLG0016` (status=batch_error, reason=KeyError) und Gegenmaßnahme ableiten**.

## Fehlerbild

- Der letzte Batchlauf brach für `DLG0016.JPG` im dual-arrow-Pfad mit `KeyError: 'img_path'` ab.
- Ursache war ein Schnittstellenbruch zwischen Dispatch und Mode-Runner: Der Dual-Arrow-Runner nutzte `kwargs["img_path"]` für den eingebetteten Raster-Fallback, der Dispatch reichte den Bildpfad aber nicht an diesen Modus weiter.

## Änderungen

- `runPreparedIterationModeImpl(...)` reicht `img_path` jetzt auch im `dual_arrow_badge`-Dispatch weiter.
- `buildIterationModeRunnersImpl(...)` entnimmt `img_path` vor dem Aufruf des eigentlichen Dual-Arrow-Runtimes aus den Wrapper-Argumenten und nutzt ihn nur für `render_embedded_raster_svg_fn`, sodass `runDualArrowBadgeIterationImpl(...)` keine unerwarteten Zusatzargumente erhält.
- Ein katalogfreier Detailtest (`ZZ_DUAL_ARROW`) sichert, dass der Dual-Arrow-Dispatch den Bildpfad an den Wrapper weitergibt.

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_iteration_dispatch_helpers.py tests/detailtests/test_iteration_mode_runtime_helpers.py::test_build_iteration_mode_runners_impl_wires_dual_arrow_detector_with_numpy_module` läuft grün.
- Ein gezielter CLI-Repro mit `--input-dir artifacts/images_to_convert/nonconvertable --start DLG0016 --end DLG0016` erreicht in dieser Umgebung keine Eingabedatei, weil die vorhandene Fixture `DLG0016.JPG` eine großgeschriebene Erweiterung besitzt und die CLI-Auswahl nur die kleingeschriebenen unterstützten Endungen meldet. Der ursprüngliche `KeyError: 'img_path'` ist durch den abgesicherten Schnittstellenfix behoben; die Groß-/Kleinschreibung der Dateiendung bleibt ein separater CLI-Auswahlhinweis.

## Ergebnis

Die DLG0016-Folgeaufgabe ist abgeschlossen: Der dokumentierte KeyError hat eine konkrete Ursache, eine Runtime-Gegenmaßnahme und einen katalogfreien Regressionstest.
