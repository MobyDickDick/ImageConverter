# Generalisierungs-Prinzipien für den ImageConverter

## Ziel
Der Konverter soll **allgemeingültig** arbeiten: Aus
1. Bildpfad/-bezeichnung und
2. Bildbeschreibung

wird ein SVG erzeugt, ohne dass dafür bildspezifische Sonderfälle im Code hinterlegt werden müssen.

## Verbindliche Regeln (No-Insellösungen)
- Keine hartcodierten Symbol-zu-Symbol-Aliaslisten (z. B. `AC0010 -> AC0100`) in Runtime-Modulen.
- Keine per Bild-ID verdrahteten Entscheidungszweige im Konvertierungsfluss.
- Heuristiken müssen regelbasiert und auf Klassen von Fällen anwendbar sein (z. B. Suffix-Normalisierung `_L/_M/_S`), nicht auf einzelne IDs.
- Falls ein Sonderfall unvermeidbar erscheint, muss stattdessen zuerst ein allgemeineres Merkmal/Regel-Set definiert werden.

## Plan-B-Sample-Auswahl (konkret für Non-Composite Runtime)
- Kandidaten dürfen nur aus dem aktuellen `base_name` und generischen Suffix-Regeln abgeleitet werden.
- Zulässig sind nur transformationsbasierte Kandidaten (z. B. root ohne Suffix, benachbarte Größen-Suffixe), keine externen ID-Mapping-Tabellen.

## Qualitätskriterium
Jede neue Verbesserung muss mindestens eine der folgenden Eigenschaften haben:
- sie erweitert die Abdeckung für **mehrere** Bildklassen,
- oder sie vereinfacht Regeln bei gleicher/verbesserter Qualität,
- oder sie entfernt bestehenden bildspezifischen Code.
