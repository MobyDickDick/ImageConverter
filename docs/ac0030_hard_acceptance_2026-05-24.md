# AC0030 Hard-Abnahme (2026-05-24)

## Ziel
Objektive Entscheidung "abgeschlossen / nicht abgeschlossen" für `AC0030.jpg`.

## Abnahmekriterien
1. **Erzeugungs-Kriterium**: Für `AC0030.jpg` existiert eine finale SVG unter `artifacts/converted_images/converted_svgs/AC0030.svg` (ohne `Failed_`-Prefix).
2. **Qualitäts-Kriterium (run-interner Fehler)**: Im Lauf-Log wird für `AC0030.jpg` ein Sample-Fehler `err <= 190` erreicht.
3. **Vergleichs-Kriterium**: Die erzeugte SVG muss in den Output-Artefakten plus Diff (`AC0030_diff.png`) vorhanden sein, damit visuelle Side-by-Side-Prüfung möglich ist.

## Ausgeführte Prüfung
- Command:
  - `PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030 --end AC0030`
- Beobachtung aus Konsole:
  - `AC0030.jpg`: `err=184.991`, `baseline=198.987` (Kriterium 2 erfüllt)

## Artefakt-Check nach Lauf
- Gefunden:
  - `artifacts/converted_images/converted_svgs/AC0030_L.svg`
  - `artifacts/converted_images/diff_pngs/AC0030_L_diff.png`
- **Nicht gefunden**:
  - `artifacts/converted_images/converted_svgs/AC0030.svg`
  - `artifacts/converted_images/diff_pngs/AC0030_diff.png`

## Entscheidung
- **Status: NICHT ABGESCHLOSSEN**.
- Begründung: Trotz gutem run-internem Fehlerwert für `AC0030.jpg` fehlen die finalen AC0030-Artefakte im Output. Damit sind Kriterium 1 und 3 derzeit nicht erfüllt.

## Sofort umsetzbarer Maßnahmenplan (direkt anschließbar)
1. **Dateiauswahl deterministisch fixieren**
   - Prüfen, warum im Bereichslauf mehrere AC0030-Varianten mehrfach verarbeitet werden und finale `AC0030.svg` nicht stabil geschrieben wird.
   - Instrumentierung in der CLI-Pipeline: pro Datei finaler Zielpfad + letzter Write-Status loggen.
2. **Output-Finalisierung für AC0030 robust machen**
   - Sicherstellen, dass bei erfolgreichem Plan-B-Sample-Pick (`status=non_composite_plan_b_sample_svg_selected`) die finale SVG für exakt diese Variante (`AC0030.svg`) persistiert bleibt.
3. **Abnahme-Test automatisieren**
   - Neuen Integrationstest ergänzen:
     - führt `--start AC0030 --end AC0030` aus,
     - assertet Existenz von `converted_svgs/AC0030.svg` und `diff_pngs/AC0030_diff.png`,
     - assertet `status != Failed_*` für AC0030.
4. **Re-Run + harte Abnahme wiederholen**
   - Nach Fix erneut den obigen Command ausführen,
   - Kriterien 1–3 erneut prüfen,
   - erst dann "abgeschlossen" markieren.
