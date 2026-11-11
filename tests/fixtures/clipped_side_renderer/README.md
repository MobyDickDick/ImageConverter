Frozen librsvg pixels for SVG-CLIPPED-SIDE-RENDERER-01, 2026-11-11.

All 26 SVG/PNG controls were saved before the rendering change, using
`python -m tools.evaluate_clipped_side_renderer --prepare ...`.
The manifest preserves SVG/PNG hashes, native object/relationship oracles,
crop sides and visible corner/side regions (derived by the external auditor).

The two original controls are exactly the unchanged additional-seed 391827
cases `clipped_rectangle_02` and `clipped_rectangle_10` from the preceding
package. Twenty-four renderer-only controls vary both gradient axes, stroke
widths 1/1.5/3 and four subpixel translations. Their inherited descriptions
are provenance, not new CLI acceptance inputs. Reference pixels use librsvg
2.62.3 / cairo 1.18.4; the measured internal renderer uses PyMuPDF 1.26.7.

Unit tests read these exact PNGs without librsvg or regeneration. The separate
audit checks both renderers. Before/after metrics, original Canny edge/profile
comparisons and all CLI denominators are retained in
`artifacts/evaluation/clipped_side_renderer_v1/summary.json`. Historical
unsuccessful attempts remain separate from the final acceptance.
