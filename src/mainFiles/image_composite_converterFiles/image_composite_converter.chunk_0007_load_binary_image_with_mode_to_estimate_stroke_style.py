def load_binary_image_with_mode(path: Path, *, threshold: int = 220, mode: str = "global") -> list[list[int]]:
    grayscale = load_grayscale_image(path)
    m = str(mode).lower()
    if m == 'global':
        return [[1 if v < threshold else 0 for v in row] for row in grayscale]
    if m == 'otsu':
        t = _compute_otsu_threshold(grayscale)
        return [[1 if v < t else 0 for v in row] for row in grayscale]
    if m == 'adaptive':
        return _adaptive_threshold(grayscale)
    raise ValueError(f"Unknown threshold mode '{mode}'.")


def render_candidate_mask(candidate: Candidate, width: int, height: int) -> list[list[int]]:
    mask = [[0 for _ in range(width)] for _ in range(height)]
    rx = max(1.0, (candidate.w + candidate.h) / 4.0) if candidate.shape == 'circle' else max(1.0, candidate.w / 2.0)
    ry = rx if candidate.shape == 'circle' else max(1.0, candidate.h / 2.0)
    inv_rx2 = 1.0 / (rx * rx)
    inv_ry2 = 1.0 / (ry * ry)
    for y in range(height):
        for x in range(width):
            if ((x - candidate.cx) ** 2) * inv_rx2 + ((y - candidate.cy) ** 2) * inv_ry2 <= 1.0:
                mask[y][x] = 1
    return mask


def _iou(a: list[list[int]], b: list[list[int]]) -> float:
    inter = union = 0
    for y in range(len(a)):
        for x in range(len(a[0])):
            av, bv = a[y][x], b[y][x]
            if av and bv:
                inter += 1
            if av or bv:
                union += 1
    return inter / union if union else 0.0


def score_candidate(target: list[list[int]], candidate: Candidate) -> float:
    return _iou(target, render_candidate_mask(candidate, len(target[0]), len(target)))


def random_neighbor(base: Candidate, scale: float, rng: random.Random) -> Candidate:
    return Candidate(base.shape, base.cx + rng.uniform(-scale, scale), base.cy + rng.uniform(-scale, scale), max(1.0, base.w + rng.uniform(-scale, scale) * 1.4), max(1.0, base.h + rng.uniform(-scale, scale) * 1.4))


def optimize_element(target: list[list[int]], init: Candidate, *, max_iter: int, plateau_limit: int, seed: int) -> tuple[Candidate, float]:
    rng = random.Random(seed)
    best = init
    best_score = score_candidate(target, best)
    scale = max(1.0, max(best.w, best.h) * 0.2)
    plateau = 0
    for _ in range(max_iter):
        cand = random_neighbor(best, scale, rng)
        s = score_candidate(target, cand)
        if s >= best_score:
            best, best_score, plateau = cand, s, 0
        else:
            plateau += 1
        if plateau > plateau_limit:
            scale = max(0.5, scale * 0.7)
            plateau = 0
    return best, best_score


def _gray_to_hex(v: float) -> str:
    g = max(0, min(255, int(round(v))))
    return f"#{g:02x}{g:02x}{g:02x}"


def estimate_stroke_style(grayscale: list[list[int]], element: Element, candidate: Candidate) -> tuple[str, str | None, float | None]:
    vals = [grayscale[y + element.y0][x + element.x0] for y,row in enumerate(element.pixels) for x,v in enumerate(row) if v]
    fill = _gray_to_hex(sum(vals) / max(1, len(vals)))
    if candidate.shape != 'circle':
        return fill, None, None
    r = max(1.0, (candidate.w + candidate.h) / 4.0)
    inner=[]; outer=[]
    for y,row in enumerate(element.pixels):
        for x,v in enumerate(row):
            if not v: continue
            d=((x-candidate.cx)**2 + (y-candidate.cy)**2) ** 0.5
            px = grayscale[y + element.y0][x + element.x0]
            if d >= r*0.84:
                outer.append(px)
            elif d <= r*0.65:
                inner.append(px)
    if outer and inner and (sum(outer)/len(outer)) < (sum(inner)/len(inner)) - 10:
        return _gray_to_hex(sum(inner)/len(inner)), _gray_to_hex(sum(outer)/len(outer)), max(1.0, r*0.2)
    return fill, None, None


