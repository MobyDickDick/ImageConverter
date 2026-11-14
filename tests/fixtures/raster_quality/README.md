# Threshold-fill regression

`threshold_fill.png` and `threshold_fill.svg` preserve the 40 × 40 source and
generated vector from the reported AC0401_L.jpg attempt with 1795 candidates
(GUI job `1732be829f164bfd8f881b0ddd451bac`, 2026-11-14).
The PNG preserves the decoded JPEG pixels; it is not a fresh vector rendering.
The SVG's grey disk has contrast exactly 25 against white; JPEG noise places
similar source pixels on either side of the old hard cutoff.

These are quality-check fixtures only. Runtime conversion never reads them.
Tests check both renderers and damaged versions of the same vector, including
missing parts, wrong shape/direction/color and displaced geometry.
