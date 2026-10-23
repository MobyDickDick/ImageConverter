# Nächstes Arbeitspaket – A3/A4 Standard-Run B-AR-01 (2026-10-02)

Dieses Paket setzt die nächste offene Rotation aus **A3 Standard-Run pro
Block** in `docs/open_tasks.md` um. Nach dem zuletzt dokumentierten
`B-AC05-01` wurde der geplante AR-Block `B-AR-01` bis zum Review ausgeführt.

## Ausführung

Der timeout-gesicherte Lauf verwendete die festgelegte Python-Toolchain, die
XML-Beschreibungen und eine deterministische Reihenfolge:

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 \
  timeout 300 python -m src.iCCModules.imageCompositeConverterCli \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir /tmp/ic-b-ar-01-20261002 \
  --start AR0021 --end AR0061 --deterministic-order
```

Der vollständige Konsolenbeleg liegt unter
`artifacts/converted_images/reports/B-AR-01_standard_run_2026-10-02.log`.
Der Prozess endete mit Exit `0` und dem regulären Abschlussmarker.

## Kurzprüfung und Review

- `24` Konvertiert-Meldungen repräsentieren `12` eindeutige Varianten; die
  Mehrfachmeldungen stammen aus den Qualitätsnachläufen.
- Alle lokal vorhandenen Varianten der zehn geplanten Basis-IDs wurden
  verarbeitet. Zusätzlich zu den Basisvarianten liegen `AR0030_1.jpg` und
  `AR0030_2.jpg` im gewählten Bereich.
- Es gab keinen Timeout, keinen Traceback, kein `conversion_failed` und keine
  `ERROR`-Meldung.
- Die `18` Warnungen betreffen ausschließlich räumlich konzentrierte
  Differenzbild-Fehlerpixel in Erst- und Nachläufen. Sie bleiben
  Qualitätsfolgepunkte, blockieren aber den stabilen Standard-Run nicht.

`B-AR-01` ist damit bis **Review** abgeschlossen. Das nächste offene Paket in
der dokumentierten A3-Blockrotation ist `B-DLG-01`.
