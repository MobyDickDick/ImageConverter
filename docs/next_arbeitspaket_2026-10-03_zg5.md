# Nächstes Arbeitspaket – ZG5 Semantik-first-Ausführungsmodus (2026-10-03)

Dieses Paket arbeitet nach ZG4 die nächste priorisierte Aufgabe aus
`docs/umsetzungscheck_bild_semantik_2026-05-15.md` ab: **Semantik-first
Execution-Mode**.

## Klärung der Eingabequellen

Die in ZG4 geprüften Rasterdimensionen stammen aus dem zu konvertierenden Bild
selbst. Es gibt keine zusätzliche Dimensionsdatei. Das erzeugte SVG ist das zu
prüfende Ergebnis und ebenfalls keine dritte Eingabequelle.

## Umsetzung

Die CLI besitzt `--execution-mode semantic-only|standard` und verwendet
`semantic-only` als sicheren Default. In diesem Modus wird jedes SVG nur aus
dem aktuellen Rasterbild und seiner zugeordneten sprachlichen Beschreibung
erzeugt. Insbesondere sind folgende zusätzliche Artefaktquellen ausgeschaltet:

- Wiederverwendung früherer Konvertierungsergebnisse,
- Übernahme aus einem Checkpoint,
- Template-Transfer aus einem anderen Bild beziehungsweise SVG.

Der bisherige inkrementelle Ablauf bleibt mit `--execution-mode standard`
bewusst als expliziter Kompatibilitätsmodus verfügbar. Der gewählte Modus wird
als `execution_mode` in der strukturierten Ablaufspur protokolliert.

### Korrektur: kumulative Reports bei mehreren Einzelaufrufen

Frühere Bestlistenzeilen bleiben im `semantic-only`-Modus ausschließlich als
Reporthistorie erhalten. Sie werden nicht für Auswahl, Optimierung oder
Wiederherstellung des neuen SVGs verwendet. Nach der aktuellen Konvertierung
werden alte und neue Reportzeilen zusammengeführt, wobei der aktuelle Lauf bei
derselben Variante Vorrang hat. Dadurch löscht eine Folge einzelner CLI-Aufrufe
nicht mehr jeweils die zuvor dokumentierten Varianten.

## Absicherung und nächster Schritt

CLI-Tests prüfen den sicheren Default, die explizite Auswahl beider Modi und
die Weitergabe des Semantik-only-Schalters an den Konvertierungslauf. Ein
zusätzlicher Bestlisten-Test sowie der schwere AC0010-/AC0100-Test sichern die
kumulative Reportführung über vier Einzelaufrufe ab. ZG5 ist damit
abgeschlossen. Die nächste priorisierte Leitaufgabe ist die robuste,
einheitliche Nicht-Erreichbarkeitsklassifikation aus P1.
