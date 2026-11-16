# Aktuelles SVG und geschützter Zeichenkontrast

[Beschreibung und Vergleichsregel](../../../docs/current_svg_reuse_and_detail_contrast_2026-11-16.md).

- [Tatsächlich gespeichertes Projekt-SVG](../../converted_images/converted_svgs/AC0130.svg)
- [Korrigierte Vorschau](corrected_preview.png)
- [Unveränderliche Studienkopie des korrigierten SVG](corrected.svg)
- [Bericht der Vorlagenanpassung](corrected.json)
- [Bericht der tatsächlichen Projektübernahme](applied_project.json)
- [Abschliessende Regressionen](verified_tests.log)
- [Kompakter Nachweis](summary.json)

Die kleinen konkreten Nutzerbeispiele sind unter
`tests/fixtures/sample_contrast/` als Regression erhalten.
Die generierten Ausgaben und vollständigen Protokolle bleiben lokal.

Für die neue Checkbox und die Backend-Wiederverwendung den laufenden Webserver
nach Abschluss aktiver Jobs über `stopWebServer.cmd` und `startWebServer.cmd`
neu starten und die Browserseite neu laden.
