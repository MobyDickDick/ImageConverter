# Nächstes Arbeitspaket – Run MT (2026-05-30)

Dieses Arbeitspaket arbeitet nach PF5/PF6 die nächste dokumentierte offene
Perception-First-Aufgabe **PF7** ab: eine Minimalbewertung, ob bekannte Glyphen
und kurze Labels ohne neue OCR-Pflichtdependency per Template-Matching erkannt
werden können.

## 1) Nächste dokumentierte Aufgabe: PF7 Text-/Glyph-Evaluation

- Anlass:
  - `docs/open_tasks.md` markierte PF7 als nächste offene
    Perception-First-Aufgabe.
  - `docs/perception_first_task_backlog_2026-05-30.md` fordert eine
    Minimalstrategie für `M`, `+`, `-` und kurze Labels, bevor ein OCR-Backend
    verpflichtend wird.
- Umsetzung:
  - `detect_text_glyph_candidates(...)` leitet optional eine ROI aus der
    Beschreibung ab, binarisiert das Bild und matched bekannte Glyph-/Label-
    Templates mit `cv2.matchTemplate`.
  - Treffer werden als `text_glyph` im bestehenden
    `perception_primitive_candidate_v1`-Contract ausgegeben.
  - Der Report `--report text-glyph-eval` schreibt JSON und CSV mit Samples,
    Confidence und Match-Entscheidung.

## 2) Gekoppelte Plan-B-/Repro-Aufgabe

- Synthetische Fixtures:
  - `glyph_m_synthetic`
  - `glyph_plus_synthetic`
  - `glyph_minus_synthetic`
  - `short_label_voc_synthetic`
- Realbild-Kopplung:
  - Wenn vorhanden, wird `artifacts/images_to_convert/AC0120_L.jpg` als realer
    Plus-/Plan-B-Kandidat mitgeführt.
- Artefakte:
  - `artifacts/evaluation/perception_text_glyph_evaluation_v1/perception_text_glyph_evaluation_report_v1.json`
  - `artifacts/evaluation/perception_text_glyph_evaluation_v1/perception_text_glyph_evaluation_samples_v1.csv`
- Ergebnis:
  - `samples=5`
  - `matched_samples=5`
  - `match_rate=1.0`
  - Keine neue Pflicht-OCR-Dependency; der Detector nutzt den bestehenden
    `cv2`/`numpy`-Pfad.

## 3) Sichernde Tests und Checks

- Befehl:
  - `python -m pytest -q tests/test_perception_text_glyph_eval.py`
- Ergebnis:
  - Exit `0`
  - `3 passed`
- Befehl:
  - `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/perception_detection_contract.py --report text-glyph-eval --output-dir artifacts/evaluation/perception_text_glyph_evaluation_v1`
- Ergebnis:
  - Exit `0`
  - JSON-Summary mit `samples=5`, `matched_samples=5` und `match_rate=1.0`.

## 4) Fazit

PF7 ist abgeschlossen: Für kleine, bekannte Zeichenklassen reicht zunächst ein
Template-Matching-Pfad ohne neue Pflichtdependency. Vollständiges OCR bleibt ein
optionaler Folgeentscheid für natürliche Labels; der nächste sinnvolle Schritt
ist **PF8**, also die Verzahnung kommender Plan-B-Pakete mit einem expliziten
Abschnitt „Perception-Lerneffekt“.
