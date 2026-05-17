# Manual conversion attempt (2026-05-17)

- Command run:
  - `python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images`
- Input set:
  - `artifacts/images_to_convert` with 1785 `.jpg/.jpeg` files.
- Runtime note:
  - Converter emitted: `OpenCV bindings requires "numpy" package.`
  - It still completed and printed: `Abgeschlossen! Ausgaben unter: artifacts/converted_images`.
- Commit policy for this task:
  - Binary output files generated during this run were intentionally reverted/removed before commit.
