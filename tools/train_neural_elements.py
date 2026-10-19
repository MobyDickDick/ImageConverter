"""Reproducible offline CNN experiment; family split precedes augmentation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterNeuralElements import CLASSES, SHAPES, chip, forward
from tools.run_anytime_benchmark import write_json, digest

DATA_SEED = 20261019


def family_image(kind, family):
    rng = np.random.default_rng(DATA_SEED+family*17+CLASSES.index(kind)*100003)
    image = np.full((64,64,3), 255, np.uint8)
    color = tuple(int(x) for x in rng.integers(15, 150, 3))
    sw = int(rng.integers(1, 5))
    a, b = int(rng.integers(12,25)), int(rng.integers(12,25))
    if kind == 'circle':
        cv2.circle(image, (32,32), a, color, sw, cv2.LINE_AA)
    elif kind == 'rectangle':
        cv2.rectangle(image, (32-a,32-b), (32+a,32+b), color, sw, cv2.LINE_AA)
    elif kind == 'triangle':
        points = np.array([[32,32-b],[32-a,32+b],[32+a,32+b]], np.int32)
        cv2.polylines(image, [points], True, color, sw, cv2.LINE_AA)
    elif kind == 'line':
        cv2.line(image, (32-a,32-b), (32+a,32+b), color, sw, cv2.LINE_AA)
    elif kind == 'text':
        # Unique source strings; no font-rendered size variant crosses a split.
        alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
        text = alphabet[family//len(alphabet)]+alphabet[family%len(alphabet)]
        font = int(rng.choice([cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX]))
        cv2.putText(image, text, (3,44), font, .9, color, max(1,sw//2), cv2.LINE_AA)
    elif family % 3 == 0:
        cv2.ellipse(image, (32,32), (24,10), int(rng.integers(0,180)), 0, 360, color, sw, cv2.LINE_AA)
    elif family % 3 == 1:
        cv2.line(image,(10,10),(54,54),color,sw,cv2.LINE_AA)
        cv2.line(image,(54,10),(10,54),color,sw,cv2.LINE_AA)
    else:
        points = np.array([[32,5],[38,22],[57,22],[42,34],[48,55],[32,43],[15,55],[21,34],[6,22],[26,22]])
        cv2.polylines(image,[points.astype(np.int32)],True,color,sw,cv2.LINE_AA)
    return image


def dataset():
    data = {split: dict(images=[], labels=[], families=[]) for split in ('train','development','holdout')}
    for index, kind in enumerate(CLASSES):
        for family in range(120):
            split = 'train' if family < 80 else 'development' if family < 100 else 'holdout'
            base = family_image(kind, family)
            for variant in range(2):
                rng = np.random.default_rng(DATA_SEED+family*193+index*19001+variant)
                size = int(rng.integers(22,100))
                image = cv2.resize(base,(size,size),interpolation=cv2.INTER_AREA)
                if variant:
                    encoded = cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,int(rng.integers(55,96))])[1]
                    image = cv2.imdecode(encoded,cv2.IMREAD_COLOR)
                foreground = np.max(255-image.astype(float),axis=2)>25
                y,x = np.where(foreground)
                cropped = image[y.min():y.max()+1,x.min():x.max()+1]
                data[split]['images'].append(chip(cropped))
                data[split]['labels'].append(index)
                data[split]['families'].append(f'{kind}-{family:03d}')
    for group in data.values():
        group['images'] = np.stack(group['images'])
        group['labels'] = np.array(group['labels'])
    return data


def fit(data, seed, epochs=35):
    rng = np.random.default_rng(seed)
    weights = {k: (rng.normal(0,.15,shape).astype(np.float32) if k in ('conv','head')
                   else np.zeros(shape,np.float32)) for k,shape in SHAPES.items()}
    moments = {k: np.zeros_like(v) for k,v in weights.items()}
    variances = {k: np.zeros_like(v) for k,v in weights.items()}
    images, labels = data['train']['images'], data['train']['labels']
    step = 0
    started = time.perf_counter()
    for epoch in range(epochs):
        for positions in np.array_split(rng.permutation(len(images)), 15):
            batch, target = images[positions], labels[positions]
            probs, (windows, conv, features) = forward(weights, batch, training=True)
            delta = probs.copy()
            delta[np.arange(len(target)), target] -= 1
            delta /= len(target)
            gradients = dict(head=features.T@delta, offset=delta.sum(axis=0))
            unpool = (delta@weights['head'].T).reshape(-1,7,7,6)
            active_delta = np.repeat(np.repeat(unpool,2,axis=1),2,axis=2)/4*(conv>0)
            gradients['conv'] = np.einsum('nxyij,nxyk->kij',windows,active_delta,optimize=True)
            gradients['bias'] = active_delta.sum(axis=(0,1,2))
            step += 1
            for key, gradient in gradients.items():
                moments[key] = .9*moments[key]+.1*gradient
                variances[key] = .999*variances[key]+.001*gradient**2
                weights[key] -= .003*(moments[key]/(1-.9**step))/(np.sqrt(variances[key]/(1-.999**step))+1e-8)
    return weights, time.perf_counter()-started


def classification(weights, group):
    predictions = forward(weights,group['images'])
    labels = group['labels']
    guessed = predictions.argmax(axis=1)
    confidence = predictions.max(axis=1)
    confusion = np.zeros((6,6),int)
    np.add.at(confusion,(labels,guessed),1)
    return dict(samples=len(labels),accuracy=float(np.mean(guessed==labels)),
                high_confidence_errors=int(np.sum((guessed!=labels)&(confidence>=.8))),
                confusion=confusion.tolist(),
                calibration_bins=[dict(lower=i/5,count=int(((confidence>=i/5)&(confidence<(i+1)/5)).sum()),
                    correct=int(((confidence>=i/5)&(confidence<(i+1)/5)&(guessed==labels)).sum())) for i in range(5)])


def train(output, seeds=(17,42,101), epochs=35):
    output.mkdir(parents=True,exist_ok=False)
    data = dataset()
    protocol = dict(data_seed=DATA_SEED,classes=list(CLASSES),epochs=epochs,seeds=list(seeds),
        architecture='16x16 -> learned 6x3x3 valid convolution -> ReLU -> 2x2 mean pool -> 294x6 softmax',
        family_split={s:sorted(set(g['families'])) for s,g in data.items()},
        augmentation='Two size/JPEG variants per source family; split before augmentation.',
        pretrained='Not attempted: no installed inference/training framework; the dependency-free small CNN is the bounded first experiment.')
    write_json(output/'training_protocol.json',protocol)
    records = []
    for seed in seeds:
        weights, seconds = fit(data,seed,epochs)
        model = output/f'model-{seed}.json'
        write_json(model,dict(schema='tiny_elements_cnn_v1',classes=list(CLASSES),
            weights={k:v.tolist() for k,v in weights.items()},training_seed=seed,
            protocol_sha256=digest(output/'training_protocol.json')))
        record = dict(seed=seed,model=model.name,sha256=digest(model),bytes=model.stat().st_size,
                      training_seconds=seconds,classification={s:classification(weights,g) for s,g in data.items()})
        records.append(record)
        write_json(output/'training.json',dict(protocol_sha256=digest(output/'training_protocol.json'),records=records))
        print(f'CNN {seed}: {seconds:.2f}s, synthetic holdout accuracy {record["classification"]["holdout"]["accuracy"]:.3f}',flush=True)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',default=[17,42,101])
    args=parser.parse_args()
    train(args.output_dir,args.seeds)


if __name__ == '__main__':
    main()
