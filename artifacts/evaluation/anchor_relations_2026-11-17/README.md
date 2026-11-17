# AC0150_1: Rechteck mit randbezogenen Linien

`comparison.png` zeigt das Original und die Ausgabe einer frischen regulären
GUI-Konvertierung, jeweils fünffach ohne Interpolation vergrössert. Die Eingabe
war das unveränderte JPEG unter dem neutralen Namen `unrelated.jpg`, mit der
unveränderten Beschreibung aus `description.txt`. Das isolierte Projekt war
anfangs leer; eine Vorlage wurde nicht angehängt.

`gui-result.svg` ist das Ergebnis, `gui-result.json` der Jobbericht und
`summary.json` enthält die kompakten Messwerte und Eingabe-/Ausgabehashes.
Der Status lautet `done`, die Qualität `passed`. Die gespeicherte Ausgabe wurde
anschliessend mit der verschärften Beziehungsprüfung unabhängig nachgeprüft.
Sie enthält zwei vollständige, gespiegelte Strichpolygone unter dem Rahmen.

Eine frühere Variante mit unabhängig veränderter unterer Linie liegt als
`before-strict-relations.svg` vor. Sie hat einen kleineren Pixelfehler, verletzt
aber die verlangte Symmetrie und wird von der aktuellen Prüfung verworfen.
Sie ist kein freigegebenes Ergebnis.

Die aktuelle Fassung besteht 396 verschiedene gezielte Tests. Die vier
Prüfprotokolle enthalten 195, 186, 26 und 12 bestandene Tests; 23 der 26
Beziehungsprüfungen waren bereits im ersten Lauf enthalten.

Die SVGs wurden ausschliesslich hier zur Prüfung abgelegt; die bestehende
Projektablage des Benutzers wurde nicht ersetzt.

[Ursache, Implementierung und Grenzen](../../../docs/anchor_relations_2026-11-17.md).
