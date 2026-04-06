from __future__ import annotations


def createDiffImageImpl(
    img_orig,
    img_svg,
    *,
    cv2_module,
    np_module,
    focus_mask=None,
):
    if img_svg.shape[:2] != img_orig.shape[:2]:
        img_svg = cv2_module.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2_module.INTER_AREA)
    orig = img_orig.astype(np_module.int16)
    svg = img_svg.astype(np_module.int16)
    dx = np_module.sum(svg - orig, axis=2, dtype=np_module.int32).astype(np_module.float32)
    norm = np_module.clip(dx / (3.0 * 255.0), -1.0, 1.0)

    mask = None
    if focus_mask is not None:
        if focus_mask.shape[:2] != img_orig.shape[:2]:
            focus_mask = cv2_module.resize(
                focus_mask.astype(np_module.uint8),
                (img_orig.shape[1], img_orig.shape[0]),
                interpolation=cv2_module.INTER_NEAREST,
            )
        mask = focus_mask > 0
        norm = np_module.where(mask, norm, 0.0)

    mean_tone = np_module.mean(np_module.concatenate((orig, svg), axis=2), axis=2).astype(np_module.float32)
    magnitude = np_module.clip(np_module.abs(norm), 0.0, 1.0)
    positive = norm >= 0.0

    up = mean_tone + magnitude * (255.0 - mean_tone)
    down = mean_tone * (1.0 - magnitude)

    diff = np_module.zeros_like(img_orig)
    diff[:, :, 0] = np_module.where(positive, up, down).astype(np_module.uint8)
    diff[:, :, 1] = np_module.where(positive, up, down).astype(np_module.uint8)
    diff[:, :, 2] = np_module.where(positive, down, up).astype(np_module.uint8)
    if mask is not None:
        diff = np_module.where(mask[:, :, None], diff, 0)
    return diff


def calculateErrorImpl(img_orig, img_svg, *, cv2_module, np_module) -> float:
    if img_svg is None:
        return float("inf")
    if img_svg.shape[:2] != img_orig.shape[:2]:
        img_svg = cv2_module.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2_module.INTER_AREA)
    return float(np_module.mean(cv2_module.absdiff(img_orig, img_svg)))
