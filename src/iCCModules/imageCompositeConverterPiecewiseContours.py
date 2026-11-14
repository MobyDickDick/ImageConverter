"""Fit arbitrary closed paint boundaries as small, jointly connected cubics.

The units of work are contour arcs, not rectangular image tiles. All arcs use
the same endpoint and tangent table. Joining is consequently exact and G1
continuous, including the closing seam. Holes remain separate subpaths of a
single even-odd paint path; artificial subdivision edges are never stroked.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class ContourFit:
    curves: list
    holes: int
    max_error: float

    @property
    def segments(self):
        return sum(len(loop) for loop in self.curves)

    def path(self):
        parts = []
        for loop in self.curves:
            parts.append('M ' + ' '.join(f'{v:.5f}' for v in loop[0][0]))
            for curve in loop:
                parts.append('C ' + ' '.join(f'{v:.5f}' for v in curve[1:].ravel()))
            parts.append('Z')
        return ' '.join(parts)


def _sample_loop(contour, scale):
    points = (contour[:, 0].astype(float)+.5)/scale
    # Suppress the upsampled pixel staircase, without rounding whole fingers.
    for _ in range(3):
        points = (np.roll(points, 1, axis=0)+2*points+np.roll(points, -1, axis=0))/4
    closed = np.vstack((points, points[0]))
    distance = np.r_[0., np.cumsum(np.linalg.norm(np.diff(closed, axis=0), axis=1))]
    count = max(16, int(np.ceil(distance[-1]/.35)))
    t = np.linspace(0, distance[-1], count, endpoint=False)
    points = np.column_stack([np.interp(t, distance, closed[:, i]) for i in range(2)])
    kernel = np.exp(-np.arange(-4, 5, dtype=float)**2/(2*1.4**2))
    kernel /= kernel.sum()
    points = sum(weight*np.roll(points, offset, axis=0)
                 for offset, weight in zip(range(-4, 5), kernel))
    tangent = np.roll(points, -2, axis=0)-np.roll(points, 2, axis=0)
    tangent /= np.maximum(1e-12, np.linalg.norm(tangent, axis=1)[:, None])
    return np.vstack((points, points[0])), np.vstack((tangent, tangent[0]))


def fit_paint_boundary(alpha, *, tolerance=.3, max_segments=120, cancelled=lambda: False):
    """Adaptively split badly fitted arcs; return None on exhausted budget.

    Alpha is a soft, raster-derived paint mask. Cubics fit subpixel level sets,
    rather than emitting staircase polygons. The limit applies to all loops.
    """
    alpha = np.asarray(alpha, dtype=float)
    if (alpha.ndim != 2 or min(alpha.shape, default=0) < 2 or max(alpha.shape) > 4096
            or not np.isfinite(alpha).all() or tolerance <= 0
            or max_segments < 4 or cancelled()):
        return None
    # Keep supersampling bounded for large masks as well as small icons.
    scale = max(1, min(8, 4096//max(alpha.shape)))
    enlarged = cv2.resize(np.clip(alpha, 0, 1).astype(np.float32), None,
                          fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    contours, hierarchy = cv2.findContours((enlarged >= .5).astype('uint8'),
                                          cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hierarchy is None:
        return None
    loops, holes, errors = [], 0, []
    used = 0
    for index, contour in enumerate(contours):
        if cancelled():
            return None
        if abs(cv2.contourArea(contour))/scale**2 < .6:
            continue
        holes += int(hierarchy[0, index, 3] >= 0)
        points, tangents = _sample_loop(contour, scale)
        curves = []

        def fit_arc(start, end):
            nonlocal used
            if cancelled() or used >= max_segments:
                raise OverflowError
            samples = points[start:end+1]
            ds = np.r_[0., np.cumsum(np.linalg.norm(np.diff(samples, axis=0), axis=1))]
            t = ds/max(ds[-1], 1e-12)
            a, b = samples[0], samples[-1]
            u, v = tangents[start], tangents[end]
            b1, b2 = 3*(1-t)**2*t, 3*(1-t)*t**2
            base = ((1-t)**3+b1)[:, None]*a + (t**3+b2)[:, None]*b
            design = np.stack((b1[:, None]*u, -b2[:, None]*v), axis=2).reshape(-1, 2)
            handles = np.linalg.lstsq(design, (samples-base).ravel(), rcond=None)[0]
            handles = np.clip(handles, min(.02, ds[-1]/6), max(.02, ds[-1]*.8))
            curve = np.array([a, a+handles[0]*u, b-handles[1]*v, b])
            predicted = base+b1[:, None]*handles[0]*u-b2[:, None]*handles[1]*v
            residual = np.linalg.norm(samples-predicted, axis=1)
            error = float(residual.max())
            if error > tolerance and end-start > 4:
                split = int(np.argmax(residual))+start
                split = max(start+2, min(end-2, split))
                fit_arc(start, split)
                fit_arc(split, end)
            elif error > tolerance:
                raise OverflowError
            else:
                used += 1
                curves.append(curve)
                errors.append(error)

        try:
            # At least four arcs per closed loop avoid degenerate coincident
            # endpoints and give each coarse quadrant its own local conversion.
            breaks = np.linspace(0, len(points)-1, 5, dtype=int)
            for start, end in zip(breaks[:-1], breaks[1:]):
                fit_arc(start, end)
        except OverflowError:
            return None
        loops.append(curves)
    return ContourFit(loops, holes, max(errors)) if loops else None
