"""Foreground overlap with a narrow transition for uncertain raster pixels."""
from __future__ import annotations


def foreground_overlap(reference_contrast, output_contrast, *, normalized_mse,
                       foreground_mse, edge_alignment):
    """Return effective and diagnostic binary IoU, without moving either image.

    JPEG noise and antialiasing make a hard cutoff at contrast 25 unstable:
    otherwise identical fills at 25 and 26 would have zero binary overlap.
    Only contrasts 15..35 receive partial membership; strong foreground and
    background stay 1 and 0. Min/max intersection and union still penalize
    missing objects and displacement, rather than dilating away their errors.
    Contrast is the maximum channel distance from the *source's* background.
    Graded overlap can improve the binary score only when the pixel and edge
    checks already meet the existing preferred-quality targets. Ordinary
    candidates keep the binary score; a pale fill cannot hide structural loss.
    """
    import numpy as np

    a = np.clip((reference_contrast - 15.) / 20., 0., 1.)
    b = np.clip((output_contrast - 15.) / 20., 0., 1.)
    union = float(np.maximum(a, b).sum())
    graded = float(np.minimum(a, b).sum() / union) if union else 1.
    ma, mb = reference_contrast > 25, output_contrast > 25
    binary_union = int(np.count_nonzero(ma | mb))
    binary = float(np.count_nonzero(ma & mb) / binary_union) if binary_union else 1.
    close_raster_match = (normalized_mse <= .0005 and foreground_mse <= .005
                          and edge_alignment >= .90)
    return (max(graded, binary) if close_raster_match else binary), binary
