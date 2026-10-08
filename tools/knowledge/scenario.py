"""Build the canonical process scenario from already evidenced process steps.

No per-method splitting, actor inference, domain-specific ordering or happy-path copy.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

SELECTORS = ('main_flow', 'alternative_flows', 'exception_flows')


def flow_selectors(flows):
    main = [flow['id'] for flow in flows if flow['type'] == 'main']
    if len(main) > 1:
        raise ValueError('scenario requires a single main flow')
    return dict(main_flow=main[0] if main else None,
                alternative_flows=[f['id'] for f in flows if f['type'] == 'alternative'],
                exception_flows=[f['id'] for f in flows if f['type'] == 'error'])


def build_scenario(metadata, steps, flows, transitions):
    """Store each step/flow once; selectors only reference their existing IDs."""
    if any(key in metadata for key in ('steps', 'flows', 'transitions', 'happy_path')):
        raise ValueError('metadata cannot contain process/path copies')
    selectors = flow_selectors(flows)
    for key in SELECTORS:
        if key in metadata and metadata[key] != selectors[key]:
            raise ValueError(key + ': selector contradicts classified flows')
    result = copy.deepcopy(metadata)
    result.update(steps=copy.deepcopy(steps), flows=copy.deepcopy(flows),
                  transitions=copy.deepcopy(transitions), **selectors)
    from validate import schema_errors
    errors = schema_errors('scenario', result)
    if errors:
        raise ValueError('; '.join(errors))
    for group in ('steps', 'flows', 'transitions'):
        ids = [row['id'] for row in result[group]]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate canonical ' + group + ' ID')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('input', 'knowledge', 'domain-tree', 'scenario-definition',
                 'source-map', 'technical-flow', 'business-rules', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--previous-knowledge', type=Path)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    from validate import load, validate
    try:
        prepared = load(args.input)
        metadata = {key: value for key, value in prepared.items()
                    if key not in {'steps', 'flows', 'transitions'}}
        artifact = build_scenario(metadata, prepared['steps'], prepared['flows'], prepared['transitions'])
        errors = validate('scenario', artifact, load(args.knowledge), load(args.domain_tree),
                          load(args.scenario_definition), load(args.technical_flow),
                          load(args.source_map), load(args.business_rules),
                          previous_knowledge=load(args.previous_knowledge) if args.previous_knowledge else None)
        if errors:
            raise ValueError('; '.join(errors))
        if args.output.exists() and not args.overwrite:
            raise ValueError('existing output requires --overwrite')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print('COMPLETED: one canonical scenario; main_flow references its flow')
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print('FAILED: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
