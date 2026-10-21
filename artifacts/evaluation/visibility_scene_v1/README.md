# Sichtbarkeitsszenen – kompakte Nachweise

`summary.json` enthält die unabhängig geprüften Entscheidungszahlen,
Rastermanifest-/Bericht-/SVG-Prüfsummen und Runtime-Quellprüfsummen der
echten CLI-Läufe. `checks.json` dokumentiert Regressionen und Bestandsschutz.

Die vollständigen Raster, SVGs und Runtime-Berichte bleiben lokal unter
`.tmp/visibility-*`; CI lädt seinen vollständigen Lauf als Artefakt hoch.
Die Zusammenfassung allein ersetzt keine erneute unabhängige Raster-/SVG-Prüfung.

Reproduktion, Grenzen und Ausgangszahl 377/1.785:
[Arbeitspaket GENERAL-SCENE-VISIBILITY-04](../../../docs/next_arbeitspaket_2026-10-21_scene_visibility.md).

Synthetische Prüfszenen erhöhen die Zahl abgenommener Katalogbilder nicht.
