"""Validate five skill outputs and cumulative knowledge checkpoints, offline."""
import argparse
import copy
from pathlib import Path
import yaml

from model import TERM_FIELDS, PROFILE
from validate import load, schema_errors, validate

INPUTS = ('domain_tree', 'scenario_definition', 'technical_flow', 'source_map', 'business_rules')
KINDS = dict(domain_tree='domain-tree', scenario_definition='scenario-definition',
             technical_flow='technical-flow', source_map='source-map', business_rules='business-rules')


def projection(data):
    """Terminology may be enriched; revision rebinding cannot rewrite earlier facts."""
    result = copy.deepcopy(data)
    result.pop('package_ref', None)
    def walk(value):
        if isinstance(value, dict):
            for field in TERM_FIELDS:
                value.pop(field, None)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(result)
    return result


def validate_run(path):
    path = Path(path)
    manifest = load(path)
    errors = schema_errors('pipeline-run', manifest)
    if errors:
        return errors
    previous = None
    upstream = {}
    for number, row in enumerate(manifest['stages'], 1):
        artifact = load(path.parent / row['artifact'])
        knowledge = load(path.parent / row['knowledge'])
        inputs = {key: load(path.parent / row[key]) for key in INPUTS if key in row}
        if artifact.get('model_profile') != PROFILE or knowledge.get('model_profile') != PROFILE:
            errors.append(f'stage {number}: structured model profile required')
        stage_errors = validate(row['kind'], artifact, knowledge, previous_knowledge=previous, **inputs)
        for key, data in inputs.items():
            stage_errors += validate(KINDS[key], data, knowledge, **{
                k:v for k,v in inputs.items() if k != key})
            old = upstream.get(KINDS[key])
            if old is not None and projection(old) != projection(data):
                stage_errors.append(f'{key}: upstream projection changed beyond terminology/revision')
        errors += [f'stage {number}: {e}' for e in stage_errors]
        previous = knowledge
        upstream[row['kind']] = artifact
        if 'scenario_definition' in inputs:
            upstream['scenario-definition'] = inputs['scenario_definition']
    return list(dict.fromkeys(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    try:
        errors = validate_run(args.manifest)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.exit(2, f'{exc}\n')
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print('Five-stage contracts, references and increments passed. Semantic source review is required.')


if __name__ == '__main__':
    main()
