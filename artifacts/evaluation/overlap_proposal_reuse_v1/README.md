# Native Vorschläge unter gemeinsamem P0-Budget wiederverwenden

Die [Paketdokumentation](../../../docs/next_arbeitspaket_2026-10-31_proposal_reuse.md)
beschreibt Umsetzung, unveränderte Gates und Abnahmegrenzen.

`summary.json` enthält zwölf gepaarte CLI-Fälle einschließlich Raster-/SVGhashes,
Vorher-/Nachher-Runtimehashes, unabhängiger Objekt-/Pixelmesswerte und der
Suchereignisse. Beide Stände bestehen 12/12; sämtliche SVGs sind bytegleich.
Die mediane überwachte Prozesszeit sinkt lokal von 2,6015 auf 1,8360 Sekunden.
Die frühere dreifache native Vermessung wird pro Bild durch eine Vermessung
und zwei exakte Wiederverwendungen ersetzt.

Die gekoppelte Variantenkohorte besteht 17/17 mit demselben Runtimehash.
`checks.json` dokumentiert Befehle, Exitcodes und Berichtshashes: 599/599
Regressionen einschließlich elf neuer Prüfungen sowie Kernprofil 42/42.

Die Zahlen stammen aus seriellen lokalen Läufen mit fünf Sekunden Bildbudget.
Keine neue reale Familienabnahme, keine Katalogzahlerhöhung und keine
nachgewiesene Reparatur der historischen drei Zeitlimitfehler. Vollständige
Rohdaten liegen lokal unter `.tmp/composition-transfer/`; die versionierten
Metadaten enthalten ihre Berichtshashes. Reproduktion siehe Paketdokumentation.
