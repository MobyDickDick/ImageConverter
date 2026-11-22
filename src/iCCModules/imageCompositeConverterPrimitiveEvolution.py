"""Population search over description-declared primitives, independent of motifs.

Random layouts, object replacement, crossover, differential mutation and local
refinement share one measured objective. Only source-bound JSON checkpoints are
loaded; they carry the population and RNG, not executable code or donor SVGs.
"""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from functools import wraps
import hashlib
import json
import math
import os
from pathlib import Path
import time

import cv2
import numpy as np

from src.iCCModules.imageCompositeConverterSceneProgram import (
    STRIDE, geometry, program_svg, relation_error, scene_program, validate_program_svg,
)
from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
    candidate_identity, current_search, pixel_quality, preferred_quality,
)
from src.iCCModules.imageCompositeConverterSearchPortfolio import progress, settings

SCHEMA='primitive_evolution_v4'


def search_binding(image,description,program,color_order='BGR'):
    return dict(schema=SCHEMA,source=hashlib.sha256(np.asarray(image).tobytes()).hexdigest(),
                shape=list(image.shape),description=description,program=program,color_order=color_order)


def memory_folder(image,description,seed,directory,color_order='BGR'):
    binding=search_binding(image,description,scene_program(description),color_order)
    key=hashlib.sha256(json.dumps([binding,seed],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return Path(directory)/key


@contextmanager
def memory_lock(folder):
    """OS-owned lock is released even when a GUI cancellation kills a worker."""
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    with (folder/'search.lock').open('a+b') as stream:
        if not stream.tell():
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError('Diese gespeicherte Suche läuft bereits in einem anderen Auftrag.') from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name=='nt':
                msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:
                fcntl.flock(stream.fileno(),fcntl.LOCK_UN)


def locked_memory(function):
    @wraps(function)
    def run(image,description,render_fn,**options):
        config=settings() or {}
        directory=options.get('directory') or config.get('primitive_memory') or config.get('directory')
        seed=options.get('seed') if options.get('seed') is not None else config.get('seed',0)
        if not directory:
            return function(image,description,render_fn,**options)
        with memory_lock(memory_folder(image,description,seed,directory,options.get('color_order','BGR'))):
            return function(image,description,render_fn,**options)
    return run


def atomic_json(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    temporary.replace(path)


@locked_memory
def evolve_primitives(image, description, render_fn, *, seconds=None, max_evaluations=None,
                      seed=None, directory=None, resume=True, on_improvement=None, initial_parameters=None,
                      color_order='BGR'):
    if color_order not in {'RGB','BGR'}:
        raise ValueError('Unsupported raster color order')
    program=scene_program(description)
    if program is None:
        raise ValueError('Diese Beschreibung wird von der freien Grundformensuche noch nicht vollständig unterstützt.')
    h,w=image.shape[:2]
    if min(w,h)<2 or max(w,h)>2048:
        raise ValueError('Die freie Grundformensuche unterstützt derzeit Bilder von 2 bis 2048 Pixeln je Seite.')
    config=settings() or {}
    session=current_search()
    if session:
        session.bind_reference(image)
    seed=seed if seed is not None else config.get('seed',0)
    budget=max_evaluations if max_evaluations is not None else config.get('budget',1000000)
    seconds=seconds if seconds is not None else config.get('policy',None).seconds if config.get('policy') else 300.
    if session:
        # Finish the durable checkpoint and hand it back before the supervising
        # process enforces the same hard image deadline.
        seconds=min(seconds,max(.001,session.limit-session.elapsed-min(5.,seconds*.10)))
    started=time.monotonic()
    rng=np.random.default_rng(seed)
    binding=search_binding(image,description,program,color_order)
    directory=Path(directory) if directory else config.get('primitive_memory') or config.get('directory')
    folder=memory_folder(image,description,seed,directory,color_order) if directory else None
    if folder:
        folder.mkdir(parents=True,exist_ok=True)
    background=np.median(np.concatenate((image[0],image[-1],image[:,0],image[:,-1])),axis=0)
    background_rgb=background[::-1] if color_order=='BGR' else background
    gray=bool(np.percentile(np.ptp(image.astype(float),axis=2),99)<10)
    target=image.astype(np.float32)/255.
    bg=background.astype(np.float32)/255.
    weight=1+5*np.max(abs(target-bg),axis=2)
    target_ink=np.clip(np.max(abs(target-bg),axis=2)*3,0,1)
    target_edges=cv2.Canny(image,40,100)>0
    target_distance=(np.minimum(cv2.distanceTransform((~target_edges).astype('uint8'),cv2.DIST_L2,3)/min(w,h),1.)
                     if target_edges.any() else np.zeros((h,w),dtype='float32'))
    count=len(program['objects']); dimension=count*STRIDE
    constrained_paint=bool(program.get('paint_claims'))
    structured=constrained_paint or any(o['kind']=='text' for o in program['objects'])
    active=[]
    for i,obj in enumerate(program['objects']):
        fields=[0,1,2,5,9]
        if obj['kind']=='text':
            active.extend(i*STRIDE+field for field in (2,3,6,7,8))
            continue
        if obj['kind']!='circle':
            fields.append(4)
        if obj['kind'] not in {'circle','square','line'}:
            fields.append(3)
        if obj['kind']!='line':
            fields.extend([6,12,15,16])
        if not gray:
            fields.extend([10,11])
            if obj['kind']!='line':
                fields.extend([7,8,13,14])
        active.extend(i*STRIDE+field for field in fields)
    population=[]; seen=set(); best=None; best_raster=None; best_valid=None; valid_raster=None
    best_passed=None; passed_raster=None
    evaluations=0; total=0; resumed=False; restarts=0
    operators=Counter(); geometry_seen=set(); trace_hash='00'*32
    previous_elapsed=0.; last_save=started; last_notice=started
    archive=[]
    local_fields=list(active); rng.shuffle(local_fields)
    local_index=0; local_scale=.08; local_direction=1.
    local_progress=False

    def repair(p):
        p=np.clip(np.asarray(p,dtype=float),0.,1.).reshape(count,STRIDE).copy()
        for obj,row in zip(program['objects'],p):
            row[2:4]=np.maximum(row[2:4],.025)
            if obj['kind'] in {'circle','square'}:
                size=row[2]*w
                row[2:4]=[size/w,size/h]
            row[4]%=1.
            if gray:
                for offset in (6,9,12):
                    row[offset:offset+3]=row[offset:offset+3].mean()
        from src.iCCModules.imageCompositeConverterScopedPaint import constrain_parameters
        p=constrain_parameters(program,p).reshape(count,STRIDE)
        # Bound the actual rotated geometry, including stroke, in original
        # source coordinates; this never clips away an inconvenient object.
        for i,obj in enumerate(program['objects']):
            s=geometry(dict(program,objects=[obj]),p[i],w,h)[obj['id']]
            if obj['kind'] in {'circle','ellipse'}:
                sx,sy=s['size']; a=s['angle']
                ext=np.array([math.hypot(sx*math.cos(a),sy*math.sin(a)),math.hypot(sx*math.sin(a),sy*math.cos(a))])/2
            else:
                ext=np.max(abs(s['points']-s['center']),axis=0)
            margin=s['stroke']/2+.01
            factor=min(1.,*((np.array([w,h])/2-margin)/np.maximum(ext,1e-6)))
            p[i,2:4]*=max(.01,factor)
            ext=ext*max(.01,factor)+margin
            p[i,:2]=np.clip(p[i,:2]*[w,h],ext,np.array([w,h])-ext)/[w,h]
        return p.ravel()

    def random_layout():
        p=rng.uniform(0,1,(count,STRIDE))
        p[:,2:4]=rng.uniform(.08,.7,(count,2))
        p[:,5]=rng.uniform(.08,.65,count)
        # Broad shared paint prior, no shape location or source contour fit.
        p[:,6:9]=rng.uniform(.4,1,(count,1))
        p[:,9:12]=rng.uniform(.1,.75,(count,1))
        return repair(p)

    def bound_group(p):
        # Fit the connected group as a whole. Clamping its children separately
        # would detach the shared anchors at the edge of the canvas.
        shapes=geometry(program,p,w,h)
        lows=[]; highs=[]
        for shape in shapes.values():
            points=(np.array([shape['center']-np.array(shape['size'])/2,
                              shape['center']+np.array(shape['size'])/2])
                    if shape['kind']=='circle' else shape['points'])
            lows.append(points.min(axis=0)-shape['stroke']/2)
            highs.append(points.max(axis=0)+shape['stroke']/2)
        low=np.min(lows,axis=0); high=np.max(highs,axis=0)
        scale=min(1.,*(((np.array([w,h])-.1)/np.maximum(high-low,1e-8))))
        offset=np.maximum(.05-low*scale,0)
        offset=np.minimum(offset,np.array([w,h])-.05-high*scale)
        p[:,:2]=(p[:,:2]*[w,h]*scale+offset)/[w,h]
        p[:,2:4]*=scale; p[:,5]*=scale
        return p.ravel()

    def join(p):
        p=p.reshape(count,STRIDE).copy()
        indices={o['id']:i for i,o in enumerate(program['objects'])}
        ordered=sorted(program['relations'],key=lambda r:r['kind']!='attached')
        # A reference can precede its definition in prose. Repeated graph
        # relaxation propagates a changed parent to all declared dependants.
        for rel in ordered*max(1,len(ordered)):
            shapes=geometry(program,p,w,h)
            aid,bid=rel['objects']; a,b=shapes[aid],shapes[bid]
            if rel['kind']=='inside':
                p[indices[bid],:2]=a['center']/[w,h]
                extent=np.linalg.norm(p[indices[bid],2:4]*[w,h])
                p[indices[bid],2:4]*=min(1.,a['size'][0]*.92/max(extent,1e-8))
            elif rel['kind']=='attached':
                angle=rel['direction'] if rel['direction'] is not None else b['angle']
                unit=np.array([math.cos(angle),math.sin(angle)])
                p[indices[bid],4]=(angle/(2*math.pi))%1
                p[indices[bid],:2]=(a['center']+unit*(a['size'][0]/2+b['size'][0]/2))/[w,h]
            else:
                pa=a['points'][1 if rel['anchors'][0]=='end' else 0]
                pb=b['points'][1 if rel['anchors'][1]=='end' else 0]
                p[indices[bid],:2]+=(pa-pb)/[w,h]
        return bound_group(p)

    # A changed seed requests a fresh search. The same seed resumes the exact
    # frontier, independently of changing upload paths and filenames.
    if folder and resume and (folder/'checkpoint.json').is_file():
        try:
            state=json.loads((folder/'checkpoint.json').read_text(encoding='utf-8'))
            if state['binding']==binding and state['seed']==seed:
                restored=[]
                for item in state['population']:
                    p=np.asarray(item['parameters'],dtype=float)
                    if (p.shape!=(dimension,) or not np.isfinite(p).all() or not np.allclose(repair(p),p)
                            or not math.isfinite(item['score']) or not 0 <= item['score'] <= 10):
                        raise ValueError('Invalid checkpoint parameters')
                    restored.append(dict(item,parameters=p))
                if not restored:
                    raise ValueError('Empty checkpoint')
                population=restored
                best=min(population,key=lambda item:(not (item.get('valid') and item.get('quality',{}).get('passed')),item['score']))
                # Persisted flags do not grant validity to other population
                # members; each must earn it again from an actual rendering.
                for item in population:
                    item['valid']=False
                best_valid=None
                rng.bit_generator.state=state['rng']
                local=state.get('local_refinement')
                if local:
                    local_fields=local['fields']; local_index=local['index']; local_scale=local['scale']
                    local_direction=local['direction']; local_progress=local['progress']
                    if (sorted(local_fields)!=sorted(active) or not 0<=local_index<len(local_fields)
                            or not .0001<=local_scale<=1 or local_direction not in {-1.,1.}):
                        raise ValueError('Invalid local refinement checkpoint')
                total=state['total_evaluations']; previous_elapsed=state['elapsed_seconds']
                seen=set(state['seen']); geometry_seen=set(state['geometry_seen'])
                trace_hash=state['trace_hash']; operators.update(state['operators'])
                restarts=state['restarts']; archive=state.get('archive',[]); resumed=True
        except (OSError,ValueError,KeyError,TypeError):
            # A malformed file is never a source of executable instructions.
            population=[]; best=None; seen=set(); geometry_seen=set()
    journal=(folder/'candidates.jsonl').open('a',encoding='utf-8',buffering=1) if folder else None
    from src.iCCModules.imageCompositeConverterDescriptionLanguage import description_assertions,validate_svg_assertions
    assertions=description_assertions(description)

    def check(svg,raster):
        quality=pixel_quality(image,raster)
        try:
            validate_program_svg(svg,program)
            validate_svg_assertions(svg,assertions)
            return quality,True
        except ValueError:
            return quality,False

    # Reloaded success flags are evidence, never a substitute for re-rendering
    # and checking the saved program against these exact source pixels.
    if resumed and best is not None:
        svg=program_svg(program,best['parameters'],w,h,background_rgb)
        best_raster,fresh=session.render_candidate(image,svg,render_fn,w,h) if session else (render_fn(svg,w,h),True)
        evaluations+=int(fresh); total+=int(fresh)
        operators['checkpoint_validation']+=int(fresh)
        if session:
            session.evaluations+=int(fresh)
        if best_raster is None:
            raise ValueError('Der gespeicherte Suchstand konnte nicht erneut gerendert werden.')
        quality,valid=check(svg,best_raster)
        best.update(quality=quality,valid=valid)
        if valid:
            best_valid=best; valid_raster=best_raster.copy()
            if quality['passed']:
                best_passed=best; passed_raster=best_raster.copy()

    def save(reason):
        if not folder or best is None:
            return
        rows=[dict(item,parameters=item['parameters'].tolist()) for item in population]
        if not any(np.array_equal(item['parameters'],best['parameters']) for item in population):
            rows.append(dict(best,parameters=best['parameters'].tolist()))
        if best_valid is not None and not any(np.array_equal(item['parameters'],best_valid['parameters']) for item in population):
            rows.append(dict(best_valid,parameters=best_valid['parameters'].tolist()))
        if best_passed is not None and not any(row['parameters']==best_passed['parameters'].tolist() for row in rows):
            rows.append(dict(best_passed,parameters=best_passed['parameters'].tolist()))
        state=dict(binding=binding,seed=seed,rng=rng.bit_generator.state,population=rows,
                   total_evaluations=total,elapsed_seconds=previous_elapsed+time.monotonic()-started,
                   seen=sorted(seen),geometry_seen=sorted(geometry_seen),trace_hash=trace_hash,
                   operators=dict(operators),restarts=restarts,archive=archive,stop_reason=reason,
                   local_refinement=dict(fields=local_fields,index=local_index,scale=local_scale,
                                         direction=local_direction,progress=local_progress))
        atomic_json(folder/'checkpoint.json',state)
        svg=program_svg(program,best['parameters'],w,h,background_rgb)
        (folder/'best.svg').write_text(svg,encoding='utf-8')
        atomic_json(folder/'solution.json',dict(binding=binding,parameters=best['parameters'].tolist(),
                    quality=best.get('quality'),validated=best.get('valid',False),seed=seed,trace_hash=trace_hash))

    def measure(p,operator):
        nonlocal evaluations,total,best,best_raster,best_valid,valid_raster,trace_hash,best_passed,passed_raster
        p=repair(p)
        if structured and program['relations']:
            # Keep declared connections on the search manifold. Otherwise a
            # harmless paint mutation can lose its valid connected branch.
            p=repair(join(p))
        svg=program_svg(program,p,w,h,background_rgb)
        identity=candidate_identity(svg)
        if identity in seen:
            return None
        seen.add(identity)
        raster,fresh=session.render_candidate(image,svg,render_fn,w,h) if session else (render_fn(svg,w,h),True)
        if raster is None:
            return None
        evaluations+=int(fresh); total+=int(fresh); operators[operator]+=1
        # Track geometry independently of changes in paint and metadata.
        shapes=geometry(program,p,w,h)
        pose=[]
        for obj in program['objects']:
            shape=shapes[obj['id']]
            values=(np.r_[shape['center'],shape['size']] if shape['kind']=='circle'
                    else shape['points'].ravel())
            pose.extend(np.round(np.r_[values,shape['stroke']],5))
        geometry_id=hashlib.sha256(np.asarray(pose).tobytes()).hexdigest()
        geometry_seen.add(geometry_id)
        trace_hash=hashlib.sha256(bytes.fromhex(trace_hash)+identity.encode()).hexdigest()
        candidate=raster.astype(np.float32)/255.
        mse=float((np.square(candidate-target).mean(axis=2)*weight).mean())
        ink=np.clip(np.max(abs(candidate-bg),axis=2)*3,0,1)
        overlap=float(np.minimum(target_ink,ink).sum()/max(1.,np.maximum(target_ink,ink).sum()))
        edges=cv2.Canny(raster,40,100)>0
        chamfer=float(target_distance[edges].mean()) if edges.any() else 1.
        distance=(np.minimum(cv2.distanceTransform((~edges).astype('uint8'),cv2.DIST_L2,3)/min(w,h),1.)
                  if edges.any() else np.ones((h,w),dtype='float32'))
        chamfer+=(float(distance[target_edges].mean()) if target_edges.any() else 0.)
        relations=relation_error(program,shapes,w,h)
        score=float(mse+.035*(1-overlap)+.04*chamfer+.12*relations)
        item=dict(parameters=p,score=score,candidate=identity)
        improved=best is None or score<best['score']
        if structured or improved or score<.025 or operator=='join_declared_anchors':
            quality,valid=check(svg,raster)
            item.update(quality=quality,valid=valid)
            if structured:
                improved=(best is None or (not valid,not quality['passed'],score)<
                          (not best.get('valid'),not best.get('quality',{}).get('passed'),best['score']))
            if valid and (best_valid is None or score<best_valid['score']):
                best_valid=item; valid_raster=raster.copy()
            if valid and quality['passed'] and (best_passed is None or score<best_passed['score']):
                best_passed=item; passed_raster=raster.copy()
            if improved:
                best=item; best_raster=raster.copy()
                if session:
                    session.measured(svg,float(quality['normalized_mse']),source=SCHEMA,scope='full_scene',valid=valid,passed=valid and quality['passed'])
                if folder and (not archive or total-archive[-1]['evaluation']>=30):
                    filename=f'variant-{total:07d}.svg'
                    (folder/filename).write_text(svg,encoding='utf-8')
                    archive.append(dict(file=filename,evaluation=total,score=score,geometry=geometry_id))
                if on_improvement and valid:
                    on_improvement(svg,raster)
        if session:
            session.evaluations+=int(fresh)
        if journal:
            journal.write(json.dumps(dict(evaluation=total,operator=operator,candidate=identity,geometry=geometry_id,
                           score=score,mse=mse,overlap=overlap,chamfer=chamfer,relations=relations,
                           parameters=np.round(p,8).tolist(),improved=improved),allow_nan=False)+'\n')
        return item

    reason='evaluation_limit'
    progress(SCHEMA,event='primitive_evolution_started',objects=program['objects'],seed=seed,resumed=resumed,
             seconds=seconds,checkpoint=str(folder) if folder else None)
    try:
        if initial_parameters is not None and not resumed:
            initial=measure(initial_parameters,'template_initialization')
            if initial:
                population.append(initial)
        # At least 32 independent layouts, none derived from measured contours.
        while evaluations<budget and time.monotonic()-started<seconds and not (session and session.reason()):
            if best and best.get('valid') and (preferred_quality(best.get('quality')) if constrained_paint
                                              else best.get('quality',{}).get('passed')):
                reason='satisfactory'; break
            if len(population)<32:
                child=random_layout(); operator='random_layout'; parent=None
            else:
                # Retain diverse basins. Selection of a branch need not improve
                # the global best, so crossing a fitness valley remains possible.
                branch=rng.random()
                valid_indices=[i for i,item in enumerate(population) if item.get('valid')]
                if branch<.3 and valid_indices:
                    parent=min(valid_indices,key=lambda i:population[i]['score'])
                elif branch<.65:
                    parent=int(rng.integers(len(population)))
                else:
                    parent=min(range(len(population)),key=lambda i:population[i]['score'])
                child=population[parent]['parameters'].copy()
                choice=rng.random(); obj=int(rng.integers(count))
                if structured and rng.random()<.45:
                    # Complete signed coordinate sweeps refine the incumbent,
                    # while the remaining operators continue exploring basins.
                    child=best['parameters'].copy()
                    field=local_fields[local_index]
                    child[field]+=local_direction*local_scale
                    if gray and field%STRIDE in {6,9,12}:
                        child[field:field+3]=child[field]
                    if local_direction<0:
                        local_index+=1
                        if local_index==len(local_fields):
                            local_index=0
                            if not local_progress:
                                local_scale*=.5
                                if local_scale<.001:
                                    local_scale=.08
                            local_progress=False
                            rng.shuffle(local_fields)
                    local_direction=-local_direction
                    operator='coordinate_refinement'
                    parent=min(range(len(population)),key=lambda i:population[i]['score'])
                elif choice<.06:
                    child=random_layout(); operator='random_layout'; restarts+=1
                elif constrained_paint and choice<.15:
                    child.reshape(count,STRIDE)[obj,4]=float(rng.integers(4))*.25
                    operator='rotate_object'
                elif choice<.15:
                    child.reshape(count,STRIDE)[obj]=random_layout().reshape(count,STRIDE)[obj]
                    operator='replace_object'
                elif constrained_paint and choice<.30:
                    row=child.reshape(count,STRIDE)[obj]
                    row[2:4]=rng.uniform(.05,.75,2)
                    row[4]=float(rng.integers(4))*.25
                    operator='replace_object_geometry'
                elif choice<.21 and count>1:
                    other=int(rng.choice([i for i in range(count) if i!=obj]))
                    child=child.reshape(count,STRIDE)
                    child[[obj,other],:6]=child[[other,obj],:6]
                    child=child.ravel(); operator='swap_object_poses'
                elif choice<.3:
                    donor=population[int(rng.integers(len(population)))]['parameters']
                    mask=np.repeat(rng.random(count)<.5,STRIDE)
                    child[mask]=donor[mask]; operator='object_crossover'
                elif choice<.43:
                    a,b=rng.choice(len(population),2,replace=False)
                    difference=population[a]['parameters']-population[b]['parameters']
                    mask=rng.random(dimension)<rng.uniform(.15,.8)
                    child[mask]+=rng.uniform(.3,.9)*difference[mask]
                    operator='differential_mutation'
                elif choice<.53 and program['relations']:
                    child=join(child); operator='join_declared_anchors'
                else:
                    # Log-uniform scale changes include large moves throughout
                    # the run, never just subpixel refinement around one seed.
                    scale=10**rng.uniform(-3.,-.35)
                    amount=1 if rng.random()<.65 else int(rng.integers(2,7))
                    fields=rng.choice(active,min(amount,len(active)),replace=False)
                    child[fields]+=rng.normal(0,scale,len(fields))
                    for field in fields:
                        offset=field%STRIDE
                        if gray and offset in {6,9,12}:
                            child[field:field+3]=child[field]
                        if offset==4 and rng.random()<.15:
                            child[field]=float(rng.integers(4))*.25
                    operator='local_mutation' if scale<.025 else 'large_mutation'
                if program['relations'] and rng.random()<.35:
                    child=join(child)
                if gray:
                    # A paint change is one intensity variable in a gray source,
                    # rather than three diluted independent channel changes.
                    child=child.reshape(count,STRIDE)
                    for offset in (6,9,12):
                        child[:,offset:offset+3]=child[:,offset:offset+3].mean(axis=1)[:,None]
                    child=child.ravel()
            previous_score=best['score'] if best is not None else float('inf')
            trial=measure(child,operator)
            if operator=='coordinate_refinement' and trial and trial['score']<previous_score:
                local_progress=True
            if trial:
                if len(population)<32:
                    population.append(trial)
                elif operator in {'random_layout','join_declared_anchors','swap_object_poses'}:
                    # Immigrants are kept even if worse than the current best.
                    protected=min(valid_indices,key=lambda i:population[i]['score']) if valid_indices else None
                    worst=max((i for i in range(len(population)) if i!=protected),key=lambda i:population[i]['score'])
                    population[worst]=trial
                elif trial['score']<population[parent]['score']:
                    population[parent]=trial
            now=time.monotonic()
            if now-last_save>=5:
                save('running'); last_save=now
            if now-last_notice>=5:
                progress(SCHEMA,event='primitive_evolution_progress',evaluations=evaluations,
                         distinct_geometries=len(geometry_seen),restarts=restarts,best_score=best['score'] if best else None,
                         elapsed_seconds=round(now-started,2),operators=dict(operators))
                last_notice=now
        else:
            reason=(session.reason() if session else None) or ('time_limit' if time.monotonic()-started>=seconds else 'evaluation_limit')
        if best_passed is not None:
            best=best_passed; best_raster=passed_raster
        elif best is not None and not best.get('valid') and best_valid is not None:
            best=best_valid
            if valid_raster is not None:
                best_raster=valid_raster
        save(reason)
    finally:
        if journal:
            journal.close()
    if best is None:
        return None
    # A complete but disconnected draft is retained in search memory, never
    # published as a description-conforming conversion.
    svg=program_svg(program,best['parameters'],w,h,background_rgb)
    raster=best_raster
    quality,valid=check(svg,raster)
    report=dict(schema=SCHEMA,program=program,parameters=best['parameters'].tolist(),evaluations=evaluations,
                total_evaluations=total,distinct_geometries=len(geometry_seen),restarts=restarts,operators=dict(operators),
                stop_reason=reason,resumed=resumed,trace_hash=trace_hash,checkpoint=str(folder) if folder else None,
                elapsed_seconds=round(time.monotonic()-started,3),quality=quality,valid=valid)
    if folder:
        atomic_json(folder/'report.json',report)
    progress(SCHEMA,event='primitive_evolution_finished',**{k:v for k,v in report.items() if k not in {'schema','program','parameters'}})
    return dict(svg=svg,rendered=raster,error=float(quality['normalized_mse']),source=SCHEMA,search_report=report,quality=quality,valid=valid)
