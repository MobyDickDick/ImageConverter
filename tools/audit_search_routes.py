"""Inventory productive fitting routes and their shared-search dependencies.

This is a conservative static reference audit, not a proof of runtime coverage.
Callbacks, branch conditions and parameter-specific semantics need behavior tests.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'src.iCCModules.imageCompositeConverter'
BOUNDARIES = {
    PREFIX+'FilledSymbols._register': 'analytic_registration',
    PREFIX+'FilledSymbols._register_steps': 'analytic_registration',
    PREFIX+'FormModels.compare_form_models': 'form_model_competition',
    PREFIX+'DescriptionRegistration.register_description_ir': 'description_multistart',
    PREFIX+'SampleAlignment.align_sample': 'template_alignment',
    PREFIX+'SvgComponents.compose_components': 'svg_components',
    PREFIX+'ConversionComposite.runCompositeIterationImpl': 'composite',
    PREFIX+'ElementValidation.validateBadgeByElementsImpl': 'semantic_element_validation',
    PREFIX+'OptimizationGlobalSearch.optimizeGlobalParameterVectorSamplingImpl': 'semantic_parameter_sampling',
    PREFIX+'TemplateTransfer.tryTemplateTransferImpl': 'legacy_template_transfer',
}


def inventory(root=ROOT):
    functions, imports, sources = {}, {}, {}
    for path in sorted((root/'src').rglob('*.py')):
        module = '.'.join(path.relative_to(root).with_suffix('').parts)
        if module.endswith('.__init__'):
            module = module[:-9]
        source = path.read_text(encoding='utf-8-sig')
        tree = ast.parse(source)
        aliases = {}
        package = module if path.name=='__init__.py' else module.rsplit('.',1)[0]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                for alias in node.names:
                    aliases[alias.asname or alias.name] = alias.name
            elif isinstance(node,ast.ImportFrom):
                base = node.module or ''
                if node.level:
                    base = '.'.join(package.split('.')[:len(package.split('.'))-node.level+1])+('.'+base if base else '')
                for alias in node.names:
                    aliases[alias.asname or alias.name] = base+'.'+alias.name
        imports[module], sources[module] = aliases, (path,source)

        def collect(nodes, prefix=''):
            for node in nodes:
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    functions[module+'.'+prefix+node.name] = (module,node)
                elif isinstance(node,ast.ClassDef):
                    collect(node.body,prefix+node.name+'.')
        collect(tree.body)

    def resolve(name, module):
        visited = set()
        for _ in range(12):
            if name in functions:
                return name
            if name in visited:
                break
            visited.add(name)
            head,_,tail = name.partition('.')
            if head in imports.get(module,{}):
                name = imports[module][head]+('.'+tail if tail else '')
                continue
            # Re-exported helper modules/functions in package __init__ files.
            prefix,_,field = name.rpartition('.')
            if field in imports.get(prefix,{}):
                name = imports[prefix][field]
                continue
            local = module+'.'+name
            if local in functions:
                return local
            # Aliased module attributes resolve through their module imports.
            for imported_module in sorted(imports,key=len,reverse=True):
                if name.startswith(imported_module+'.'):
                    rest = name[len(imported_module)+1:]
                    head,_,tail = rest.partition('.')
                    if head in imports[imported_module]:
                        name = imports[imported_module][head]+('.'+tail if tail else '')
                        break
            else:
                break
        return None

    def dotted(node):
        if isinstance(node,ast.Name):
            return node.id
        if isinstance(node,ast.Attribute):
            value = dotted(node.value)
            return value+'.'+node.attr if value else None
        return None

    edges = {}
    for symbol,(module,node) in functions.items():
        refs = set()
        for child in ast.walk(node):
            name = dotted(child)
            target = resolve(name,module) if name else None
            if target and target != symbol:
                refs.add(target)
        edges[symbol] = refs

    def closure(symbol):
        visited, pending = set(), [symbol]
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            if current in BOUNDARIES and current != symbol:
                continue
            pending.extend(edges.get(current,()))
        return visited

    roots = set()
    for module,entry in ((PREFIX+'NonCompositeRuntime','runNonCompositeIterationImpl'),
                         (PREFIX+'SemanticBadgeRuntime','runSemanticBadgeIterationImpl'),
                         (PREFIX+'DualArrowRuntime','runDualArrowBadgeIterationImpl')):
        reachable = closure(module+'.'+entry)
        for alias,target in imports[module].items():
            if alias.startswith('fit_'):
                resolved = resolve(target,module)
                if resolved and resolved in reachable:
                    roots.add(resolved)
    roots.update(BOUNDARIES)
    roots.add('src.imageConverterSample.refine')
    rows = []
    for symbol in sorted(roots):
        visited = closure(symbol)
        boundaries = sorted({BOUNDARIES[v] for v in visited if v in BOUNDARIES})
        module,node = functions[symbol]
        path,source = sources[module]
        # Flags describe only the entry function's own body, not every branch.
        own = ast.get_source_segment(source,node) or ''
        rows.append(dict(symbol=symbol,path=path.relative_to(root).as_posix(),line=node.lineno,
            mechanism=boundaries or ['custom_fitter'],
            direct_seed=('proposal_rng' in own or 'seed=' in own or 'effective_seed' in own),
            direct_render_tracking='render_candidate' in own,
            portfolio_disabled='allow_portfolio=False' in own,
            reference_closure_size=len(visited),
            behavior_verified=False))
    return dict(schema_version='search_route_audit_v1',
        method='Static function/import references; callback resolution and branch execution are not proven.',
        entry_points=['GUI jobs/CLI/batch via IterationDispatch','GUI uploaded/current SVG via imageConverterSample.refine',
                      'Explicit SVG components via SvgComponents.compose_components'],
        route_count=len(rows), mechanisms=dict(Counter(m for row in rows for m in row['mechanism'])),routes=rows,
        excluded_productive_recovery=['src.imageConverterRecovery.recover (explicit description-only no-op)',
            'NativeSearch/StructureSearch/Fallback* research helpers (no productive continuation call)'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/evaluation/search_routes_2026-11-21/manifest.json')
    args = parser.parse_args()
    report = inventory()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('route_count','mechanisms')},ensure_ascii=False))


if __name__=='__main__':
    main()
