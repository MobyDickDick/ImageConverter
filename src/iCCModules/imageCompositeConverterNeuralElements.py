"""Optional, offline-trained tiny CNN. Predictions are proposals, never gates.

The region generator is deliberately analytic: disconnected foreground boxes
and grouped text-like regions. It cannot separate touching/occluded instances.
No training data, reference vectors or executable model formats are loaded.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

import cv2
import numpy as np

CLASSES = ('circle', 'rectangle', 'triangle', 'line', 'text', 'unknown')
SHAPES = {'conv': (6, 3, 3), 'bias': (6,), 'head': (294, 6), 'offset': (6,)}
CONFIDENCE = .80


def chip(image):
    """Aspect-preserving 16px foreground crop, shared by training/inference."""
    pixels = np.asarray(image)
    if pixels.ndim == 3:
        pixels = np.max(255-pixels.astype(np.float32), axis=2)/255
    else:
        pixels = pixels.astype(np.float32)/255
    h, w = pixels.shape
    scale = 14/max(h, w)
    small = cv2.resize(pixels, (max(1, round(w*scale)), max(1, round(h*scale))),
                       interpolation=cv2.INTER_AREA)
    result = np.zeros((16, 16), np.float32)
    y, x = (16-small.shape[0])//2, (16-small.shape[1])//2
    result[y:y+small.shape[0], x:x+small.shape[1]] = small
    return result


def forward(weights, batch, *, training=False):
    windows = np.lib.stride_tricks.sliding_window_view(batch, (3, 3), axis=(1, 2))
    conv = np.einsum('nxyij,kij->nxyk', windows, weights['conv'], optimize=True)+weights['bias']
    active = np.maximum(conv, 0)
    pooled = active.reshape(-1, 7, 2, 7, 2, 6).mean(axis=(2, 4)).reshape(-1, 294)
    logits = pooled@weights['head']+weights['offset']
    exp = np.exp(logits-logits.max(axis=1, keepdims=True))
    probabilities = exp/exp.sum(axis=1, keepdims=True)
    return (probabilities, (windows, conv, pooled)) if training else probabilities


def load_model(path):
    path = Path(path)
    if path.stat().st_size > 200_000:
        raise ValueError('Neural model exceeds 200 KB')
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get('schema') != 'tiny_elements_cnn_v1' or data.get('classes') != list(CLASSES):
        raise ValueError('Unsupported neural model schema/classes')
    weights = {key: np.asarray(data['weights'][key], dtype=np.float32) for key in SHAPES}
    if any(weights[k].shape != shape or not np.isfinite(weights[k]).all()
           or np.abs(weights[k]).max() > 100 for k, shape in SHAPES.items()):
        raise ValueError('Invalid neural weights')
    return weights, hashlib.sha256(raw).hexdigest()


def region_boxes(image):
    mask = (np.max(255-image.astype(float), axis=2) > 25).astype(np.uint8)
    # CCOMP promotes interior islands (e.g. text) to separate outer contours.
    # Hole contours are excluded, so a small ring is not counted twice.
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for i,c in enumerate(contours)
             if hierarchy[0][i][3] == -1 and cv2.contourArea(c) >= 3]
    grouped = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 7), np.uint8))
    count, _, stats, _ = cv2.connectedComponentsWithStats(grouped)
    boxes += [tuple(map(int, s[:4])) for s in stats[1:] if s[4] >= 8]
    chosen = []
    for box in sorted(set(boxes), key=lambda b: -b[2]*b[3]):
        x, y, w, h = box
        if min(w, h) < 2:
            continue
        if any(box_iou(box, other) > .65 for other in chosen):
            continue
        chosen.append(box)
        if len(chosen) == 64:
            break
    return chosen


def box_iou(a, b):
    x, y = max(a[0], b[0]), max(a[1], b[1])
    area = max(0, min(a[0]+a[2], b[0]+b[2])-x)*max(0, min(a[1]+a[3], b[1]+b[3])-y)
    return area/max(1, a[2]*a[3]+b[2]*b[3]-area)


def detect(image, weights):
    boxes = region_boxes(image)
    if not boxes:
        return []
    batch = np.stack([chip(image[y:y+h, x:x+w]) for x, y, w, h in boxes])
    probabilities = forward(weights, batch)
    return [dict(kind=CLASSES[int(p.argmax())], confidence=float(p.max()),
                 bbox=list(box), probabilities=p.tolist()) for box, p in zip(boxes, probabilities)]


def runtime_proposals(image):
    """Lazy initialization inside the supervised image deadline; safe fallback."""
    from src.iCCModules.imageCompositeConverterSearchPortfolio import settings
    config = settings()
    if not config or not config.get('neural_model'):
        return []
    identity = hashlib.sha256(np.ascontiguousarray(image).tobytes()).hexdigest()
    cache = config.setdefault('_neural_predictions', {})
    if identity in cache:
        return cache[identity]
    started = time.perf_counter()
    observation = dict(enabled=True, model_sha256=None, initialized=False,
                       initialization_seconds=0., inference_seconds=0., detections=[],
                       scene_candidates=0, scene_selected=False)
    try:
        cached = config.get('_neural_loaded')
        if cached is None:
            cached = load_model(config['neural_model'])
            config['_neural_loaded'] = cached
            observation['initialized'] = True
        observation['initialization_seconds'] = time.perf_counter()-started
        weights, observation['model_sha256'] = cached
        inference = time.perf_counter()
        observation['detections'] = detect(image, weights)
        observation['inference_seconds'] = time.perf_counter()-inference
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        observation['error'] = type(exc).__name__+': '+str(exc)
    observation['total_seconds'] = time.perf_counter()-started
    config.setdefault('neural_observations', []).append(observation)
    cache[identity] = observation['detections']
    return observation['detections']


def scene_alternatives(mask, pixels, detections):
    """Use CNN classes/positions to propose parameters; retain analytic choices."""
    x, y, w, h = cv2.boundingRect(mask)
    matches = [d for d in detections if d['confidence'] >= CONFIDENCE
               and d['kind'] in ('circle', 'rectangle') and box_iou(d['bbox'], (x,y,w,h)) > .8]
    if not matches:
        return []
    # Require the same single hollow component as the outline scene contract.
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None or sum(r[3] == -1 for r in hierarchy[0]) != 1 or len(contours) != 2:
        return []
    color = np.median(pixels[mask.astype(bool)], axis=0)
    perimeter = 2*(w+h) if matches[0]['kind'] == 'rectangle' else np.pi*(w+h)/2
    sw = max(.8, min(min(w,h)/4, float(mask.sum())/max(1, perimeter)))
    return [(d['kind'], [x+sw/2, y+sw/2, w-sw, h-sw, sw], color) for d in matches]
