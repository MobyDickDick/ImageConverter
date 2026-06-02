# Nächstes Arbeitspaket – Run NJ (2026-06-01)

Dieses Arbeitspaket bearbeitet den gemeldeten AC0812-Laufzeitpfad und hält die
Folgekorrektur zum isolierten SVG-Renderer fest. Der Fokus lag auf
`AC0812_L/M/S`, weil diese Varianten nur aus einem linken horizontalen Arm und
einem Kreis bestehen, aber im pytest-/isolierten Renderpfad unverhältnismäßig
viele nahezu identische Render-Subprozesse starteten.

## 1) Befund

- Der isolierte SVG-Renderer wurde unter pytest automatisch aktiviert. Der
  Render-Subprozess erbte jedoch nur die Prozessumgebung, nicht die zur Laufzeit
  ergänzten Vendor-`site-packages` aus `sys.path`; dadurch konnte der Child in
  dieser Umgebung `numpy` verfehlen und finale Badge-Renderings als
  `render_failure` protokollieren.
- Sobald der Child korrekt startete, blieb AC0812 trotzdem unnötig langsam: Die
  lokalen Badge-Bracketing-Schritte und der globale Vektor-Sampler erzeugten bei
  den kleinen line/circle-SVGs viele Renderaufrufe, obwohl die Geometrie bereits
  durch den lokalen Kreis-/Arm-Fit vollständig abgedeckt ist.

## 2) Umsetzung

- Der Render-Subprozess erhält nun ein aus dem aktuellen `sys.path` aufgebautes
  `PYTHONPATH`, damit Vendor-Abhängigkeiten wie `numpy`, `cv2` und `fitz` im
  Child verfügbar bleiben.
- Für kleine, einfache SVGs mit ausschließlich `line`/`circle`/`rect`/`ellipse`
  nutzt der implizite pytest-Isolationsmodus den schnellen Inprocess-Renderer;
  explizit per `IMAGE_CONVERTER_ISOLATE_SVG_RENDER=...` angeforderte Isolation
  bleibt unverändert isoliert.
- AC0812-Plain-Badges deaktivieren den globalen Suchsampler und begrenzen den
  Semantic-Badge-Validierungslauf auf eine lokale Runde. Die Varianten bestehen
  nur aus Arm + Kreis; weitere Runden wiederholten überwiegend teure Renderproben
  ohne zusätzlichen semantischen Nutzen.

## 3) Ergebnis / Nachweis

- Der gezielte AC0812-Pytest-Repro läuft wieder grün und sank im lokalen Lauf von
  einem zuvor beobachteten isolierten Langlauf von ca. `38.11s` auf `0.84s` für
  die beiden gezielten Tests (`test_finalize_ac0812...` +
  `test_ac08_semantic_anchor_variants_ac0812_only`).
- Der echte Konvertierungs-Kurzlauf für `AC0812_L/M/S` erzeugt für alle drei
  Varianten wieder SVGs mit `status=semantic_ok`:
  - `AC0812_L`: `0.309s`, SVG vorhanden, `status=semantic_ok`
  - `AC0812_M`: `0.286s`, SVG vorhanden, `status=semantic_ok`
  - `AC0812_S`: `0.300s`, SVG vorhanden, `status=semantic_ok`

## 4) Plan-B-/Regressionsteil

- Neue Regressionen sichern ab, dass der Render-Child den aktuellen Runtime-
  `PYTHONPATH` erbt, dass einfache pytest-SVGs nicht mehr unnötig einen
  Subprozess starten und dass AC0812-Plain-Badges den globalen Sampler
  deaktivieren.
- Der kostenintensive Gesamt-Gate bleibt weiterhin für CI/gezielte Folgeläufe
  delegiert; lokal wurden nur die AC0812-/Renderer-Repros und ein realer
  AC0812_L/M/S-Kurzlauf ausgeführt.
