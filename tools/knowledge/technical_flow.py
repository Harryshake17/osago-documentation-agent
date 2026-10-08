"""Construct and write a canonical technical model from already evidenced facts.

No code discovery, actor inference, business reconstruction or legacy ID rewriting.
"""
import argparse
import copy
import json
from pathlib import Path
import sys


def build_flow(metadata, nodes, relations):
    """One canonical node collection; implementation/source/claim refs live on it."""
    if any(key in metadata for key in ('nodes','steps','relations')):
        raise ValueError('metadata cannot contain node/step/edge collections')
    result=copy.deepcopy(metadata)
    result.update(nodes=copy.deepcopy(nodes),relations=copy.deepcopy(relations))
    if result.get('analysis_profile')!='execution-path-v1':
        raise ValueError('new technical flow requires execution-path-v1 and detailed nodes')
    from validate import schema_errors
    errors=schema_errors('technical-flow',result)
    if errors: raise ValueError('; '.join(errors))
    ids=[node['id'] for node in result['nodes']]
    if len(ids)!=len(set(ids)): raise ValueError('duplicate canonical technical node ID')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('input','knowledge','domain-tree','scenario-definition','source-map','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--previous-knowledge',type=Path)
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args()
    from validate import load,validate
    try:
        prepared=load(args.input)
        metadata={k:v for k,v in prepared.items() if k not in {'nodes','relations'}}
        artifact=build_flow(metadata,prepared['nodes'],prepared['relations'])
        errors=validate('technical-flow',artifact,load(args.knowledge),load(args.domain_tree),
            load(args.scenario_definition),source_map=load(args.source_map),
            previous_knowledge=load(args.previous_knowledge) if args.previous_knowledge else None)
        if errors: raise ValueError('; '.join(errors))
        if args.output.exists() and not args.overwrite: raise ValueError('existing output requires --overwrite')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print('COMPLETED: canonical nodes; no steps projection')
        return 0
    except (ValueError,KeyError,TypeError,OSError) as error:
        print('FAILED: '+str(error),file=sys.stderr)
        return 1

if __name__=='__main__': sys.exit(main())
