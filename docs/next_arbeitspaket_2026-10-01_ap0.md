# Nächstes Arbeitspaket – AP0 Resume-Provenienz und Abschlussmanifest (2026-10-01)

Dieses Paket setzt den infrastrukturellen Teil von **AP0** aus
`next_arbeitspakete_aus_artifacts_2026-10-01.md` um. Ein langer Kataloglauf kann
damit seinen Run-Bezug über einen Abbruch hinweg behalten und erst nach der
Finalisierung als abgeschlossen gelten.

## Umsetzung

- Jeder neue Lauf erhält eine `run_id` und `started_at`. Beim expliziten
  Checkpoint-Resume werden beide Werte aus dem vorhandenen Checkpoint
  übernommen.
- Vor dem Resume werden Checkpoint, Result-Map, Fehlerliste und vorhandene
  Optimierungs-Telemetrie unter `reports/resume_snapshots/<run_id>/` unverändert
  gesichert.
- Result-Map und Checkpoint werden über eine temporäre Datei, `fsync` und
  atomaren Dateiaustausch geschrieben. Der Checkpoint wird zuletzt ersetzt und
  verweist deshalb nur auf eine vollständig geschriebene Result-Map.
- Nach der Finalisierung entsteht `conversion_run_manifest.json` mit Run-ID,
  Seed, Start-/Endzeit, Eingangs- und Ergebniszählern sowie getrennten
  fachlichen Fehlern, technischen Fehlern und Timeouts. Erst danach erhält der
  Checkpoint `stage=complete` und einen Verweis auf dieses Manifest.
- Die finalisierte Result-Map wird unmittelbar vor Manifest und finalem
  Checkpoint erneut geschrieben, damit Statusänderungen aus der
  Abschlussprüfung nicht nur im Speicher verbleiben.

## Verhalten bei Resume

Der vorhandene Opt-in bleibt unverändert: `ICC_RESUME_FROM_CHECKPOINT=1`
aktiviert die Wiederaufnahme. Bereits bestätigte Dateinamen werden aus der
Result-Map partitioniert und nicht erneut konvertiert. Ohne gültige Run-ID in
einem historischen Checkpoint wird eine neue Run-ID erzeugt; damit werden alte
Artefakte nicht stillschweigend als derselbe Lauf ausgegeben.

## Sicherung

- Neue Unit-Tests prüfen atomaren JSON-Austausch, unveränderliche
  Resume-Snapshots und die getrennten Abschlusszähler.
- Die bestehenden Checkpoint-, Initial-Pass- und Quality-Pass-Tests sichern,
  dass Partitionierung und inkrementelle Hooks kompatibel bleiben.

## Verbleibender operativer Schritt

Der vorliegende Repository-Snapshot enthält nicht den außerhalb des Repos
liegenden, unterbrochenen produktiven Ausgabebaum. Der konkrete Kataloglauf mit
`run_seed=529189183` muss daher in dessen ursprünglichem Output-Verzeichnis mit
`ICC_RESUME_FROM_CHECKPOINT=1` gestartet werden. Die hier implementierte
Infrastruktur erzeugt dabei automatisch den Vorher-Snapshot und das
Abschlussmanifest. AP1/AP2 sollten erst auf diesem gesicherten Stand ausgeführt
werden.
