# Stabilization Workflow (2-Spur-Modell)

Dieses Verzeichnis trennt bewusst zwischen:

- **Next Iteration (work):** neue Änderungen, Bugfixes, Experimente.
- **Secured Iteration (stable):** verifizierte, reproduzierbare Zwischenstände.

## Schnellstart

1. Iterations-ID wählen (z. B. `iter-2026-05-17-a`).
2. Evidence-Struktur anlegen:
   ```bash
   python stabilization/scripts/init_iteration.py --id iter-2026-05-17-a
   ```
3. Inputs in `stabilization/evidence/<ITERATION>/input/` ablegen.
4. Konvertierung laufen lassen, Outputs in `.../output/` ablegen.
5. Prüfen und Report ausfüllen (`report.md`).
6. Hashes erzeugen:
   ```bash
   python stabilization/scripts/generate_checksums.py --id iter-2026-05-17-a
   ```
7. Wenn alle Gates erfüllt sind: Tag setzen und Snapshot exportieren.

## Empfohlene Git-Konvention

- Arbeitsbranch: `work/<kurzname>`
- Gesicherter Tag: `stable/<ITERATION>`

Beispiel:
```bash
git tag stable/iter-2026-05-17-a
```

## Snapshot/Export (wegkopieren)

Erzeugt ein portables Archiv mit:
- Input-Bildern
- Output-Bildern
- Checksums
- Report
- aktueller Commit-ID

```bash
python stabilization/scripts/export_iteration.py \
  --id iter-2026-05-17-a \
  --dest /tmp/imageconverter-archive
```

> Der Export soll auf ein externes Ziel kopiert werden (NAS/Cloud/USB), damit der gesicherte Stand unabhängig vom Arbeitsrepo verfügbar bleibt.
