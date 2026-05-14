#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def metrics(gt, pred):
    gt_counts = Counter((x["image_id"], x["type"]) for x in gt)
    pred_counts = Counter((x["image_id"], x["type"]) for x in pred)

    types = sorted({k[1] for k in gt_counts} | {k[1] for k in pred_counts})
    out = {}
    for t in types:
        gt_t = sum(v for (img, typ), v in gt_counts.items() if typ == t)
        pred_t = sum(v for (img, typ), v in pred_counts.items() if typ == t)
        tp = 0
        for key, g in gt_counts.items():
            if key[1] == t:
                tp += min(g, pred_counts.get(key, 0))
        fp = pred_t - tp
        fn = gt_t - tp
        precision = tp / pred_t if pred_t else 0.0
        recall = tp / gt_t if gt_t else 0.0
        out[t] = {"tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 4), "recall": round(recall, 4)}
    return out


if __name__ == "__main__":
    gt = load("artifacts/evaluation/primitive_inventory_v1/ground_truth.json")
    pred = load("artifacts/evaluation/primitive_inventory_v1/predictions.json")
    result = metrics(gt, pred)
    out_path = Path("artifacts/evaluation/primitive_inventory_v1/metrics.json")
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
