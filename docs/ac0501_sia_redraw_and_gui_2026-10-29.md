# AC0501_S_sia: Nachzeichnung und GUI-Korrekturen

Das SIA-Bild zeigt oben eine quadratische Kelle mit beiden Diagonalen,
mittigem Stiel, kleinem rundem Gelenk darunter und einer von links oben
nach rechts unten verlaufenden Klappenlinie. Das Gelenk liegt entsprechend
der bereitgestellten Vorlage vor der schrägen Linie. Die Auflösung 20 × 40
Pixel erklärt den nahezu quadratischen Rastereindruck des kleinen Kreises.

Die bereitgestellte Inkscape-Datei bleibt unverändert unter `artifacts/samples/`.
Die [neue SVG](../artifacts/converted_images/converted_svgs/AC0501_S_sia.svg)
verwendet ein echtes Quadrat, einen echten Kreis und drei native Pfade.
Quadratrand und beide Diagonalen haben dieselbe Konturfarbe; der Stiel ist
mittig angeschlossen und die Klappenlinie läuft durch die Gelenkmitte.
Die Geometrie wurde anhand der Nutzervorlage festgelegt und ihre gemeinsamen
Parameter an den Originalpixeln registriert. Dies ist eine ausdrücklich
vorlagengestützte Nachzeichnung, keine neue automatische Familienabnahme.

Die strengen unveränderten Pixelgates bestehen mit MuPDF und unabhängig
mit librsvg. Foreground-IoU: 0,914474 / 0,895833, Kantenausrichtung:
0,914557 / 0,899068, normierter MSE: 0,000405 / 0,000424.
Keine Änderung der Katalogerfolgszahl oder pauschale Abnahme anderer Größen.

Die bisherigen GUI-Aufträge belegen, dass der manuell eingegebene Text beim
Konverter ankam. Die weiße Ausgabe enthält jedoch fast vollständig außerhalb
der Zeichenfläche liegende Formen und war aufgrund von CLI-Exitstatus und
Ausgabeordner fälschlich als bestanden markiert. Die GUI rendert gespeicherte
Ausgaben jetzt gegen das tatsächliche Original nach. Leere/außerhalb liegende
Ergebnisse werden nicht angeboten; andere negative Entwürfe bleiben als
solche gekennzeichnet. Auch alte grüne Aufträge ohne diesen Nachweis werden
beim Serverstart nachgeprüft. Originaldateien und frühere Ergebnisse bleiben erhalten.

Katalogkorrektur: Neun SIA-Dateien in beiden XML-Katalogen erhalten eine
eigenständige Bildbeschreibung mit `beschreibung_modus="ersetzen"`. Die
anderen Varianten bleiben bei ihrer tatsächlich anders aussehenden
Rechteckdarstellung. Ohne diesen expliziten Modus bleiben Bildbeschreibungen
wie zuvor Ergänzungen; die Ersetzung verändert keine Familien-Aliase.
Die GUI merkt sich zuletzt gestartete eigene Beschreibungen anhand des
Bildinhalts, unabhängig vom Dateinamen.

Sample-Import: Inkscape-/Sodipodi-Ansichten und nicht sichtbare Metadaten
werden entfernt. Sichtbare Geometrie, Transformationen und Inline-Stile
bleiben erhalten. Aktive Inhalte, Fremdelemente und externe Ressourcen
bleiben ausgeschlossen. Eine bereits unter den Pixelgates akzeptierte Vorlage
wird unverändert übernommen, damit weitere Einzelpixeloptimierung das
Quadrat, die Anschlüsse oder gemeinsame Farben nicht verformt.

Die unveränderte Nutzervorlage lässt sich jetzt laden und verbessern,
bleibt im konkreten generischen Sample-Lauf bei IoU 0,725352 allerdings
korrekt ein Entwurf. Die neue Nachzeichnung besteht bereits vor der Suche;
der echte GUI-Auftrag übernimmt sie mit einer Prüfung und ohne Geometrieänderung.
Der geprüfte Auftrag steht in der lokalen GUI bereit. Für dieses Motiv die
Nachzeichnung als **Sample-SVG** verwenden; die reine Beschreibungssuche
rekonstruiert diese Kombination weiterhin nicht zuverlässig.

Prüfung: GUI-/Sample-/Nachzeichnungsblock 41 bestanden, zusätzliche
Beschreibungsregression 8 bestanden, Kernprofil 42 bestanden; Exit 0.
Bild-ID-Scanner: 0 Vorkommen, Exit 0. Lokaler HTTP-Auftrag und ausgelieferte
SVG geprüft. [Kompakte Evidenz](../artifacts/evaluation/square_damper_redraw_v1/README.md).
