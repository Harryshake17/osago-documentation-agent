"""Durable workflow control for existing skills. No source access or domain reasoning."""
import argparse
import copy
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml
from audit import check_report, digest
from glossary import empty_glossary, glossary_errors, merge
from model import PROFILE, increment_errors
from pipeline import projection
from validate import load, schema_errors, validate
from pipeline_gates import PipelineGateError, effective_gates, mandatory_gates, run_gate

ROOT = Path(__file__).resolve().parents[2]
from paths import skill_resource

DEFAULT_PIPELINE = skill_resource('osago-documentation-orchestrator', 'references', 'pipeline.yaml')
SAFE_ID = re.compile(r'^[a-z0-9][a-z0-9-]{0,63}$')
SCHEMA_ALIASES = {'knowledge':'knowledge-package', 'validation':'validation-report', 'report':'validation-report',
                  'gaps':'validation-gaps', 'documentation-meta':'documentation-manifest'}
VALIDATE_INPUTS = {'domain-tree':'domain_tree', 'scenario-definition':'scenario_definition',
                   'source-map':'source_map', 'technical-flow':'technical_flow', 'business-rules':'business_rules'}


class StateChangedError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def require(errors):
    if errors:
        raise ValueError('\n'.join(dict.fromkeys(errors)))


def safe_path(root, relative):
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('artifact path escapes run/attempt directory')
    return path


def resolve_skill_path(name):
    return str(skill_resource(name, 'SKILL.md'))


def content_hash(path, schema):
    return digest(load(path)) if schema else hashlib.sha256(Path(path).read_bytes()).hexdigest()


def correction_hash(path):
    """A revision bump alone cannot stand in for applying a human correction."""
    data=copy.deepcopy(load(path))
    if isinstance(data,dict):
        data.pop('revision',None)
        if isinstance(data.get('package_ref'),dict):
            data['package_ref'].pop('revision',None)
    return digest(data)


def records(data):
    """Index declared IDs for mechanical provenance checks, without interpreting values."""
    result={}
    def visit(value):
        if isinstance(value,dict):
            if isinstance(value.get('id'),str):
                existing = result.get(value['id'])
                if isinstance(existing, dict):
                    # Merge properties so richer objects (e.g. detailed nodes) are not overwritten by lightweight projection steps
                    merged = dict(existing)
                    merged.update(value)
                    result[value['id']] = merged
                else:
                    result[value['id']]=value
            for child in value.values(): visit(child)
        elif isinstance(value,list):
            for child in value: visit(child)
    visit(data)
    return result


def binding(root, path, schema):
    path = Path(path).resolve()
    relative = path.relative_to(Path(root).resolve()).as_posix()
    if not path.is_file():
        raise ValueError('missing output: ' + relative)
    data=load(path) if schema else path.read_bytes()
    if schema:
        require(schema_errors(schema,data))
    hashed=digest(data) if schema else hashlib.sha256(data).hexdigest()
    return dict(path=relative, content_hash=hashed, schema=schema)


def read_binding(root, ref):
    path = safe_path(root, ref['path'])
    if not path.is_file():
        raise ValueError('missing artifact: ' + ref['path'])
    data=load(path) if ref['schema'] else path.read_bytes()
    if ref['schema']:
        require(schema_errors(ref['schema'],data))
    hashed=digest(data) if ref['schema'] else hashlib.sha256(data).hexdigest()
    if hashed != ref['content_hash']:
        raise ValueError('artifact changed after acceptance: ' + ref['path'])
    return path,data


def check_binding(root, ref):
    return read_binding(root,ref)[0]


def save_data(path, data):
    """Replace a single manifest atomically; never removes stage artifacts."""
    path = Path(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding='utf-8')
    temporary.replace(path)


def pipeline_errors(config):
    errors = schema_errors('documentation-pipeline', config)
    if errors:
        return errors
    specs = {s['id']:s for s in config['stages']}
    if len(specs) != len(config['stages']):
        errors.append('pipeline: duplicate stage ID')
    seen = set()
    for s in config['stages']:
        if not SAFE_ID.fullmatch(s['id']):
            errors.append('pipeline: invalid stage ID')
        if not set(s['depends_on']) <= seen:
            errors.append(s['id'] + ': dependencies must precede the stage (no cycles)')
        if s['type']=='skill' and (not s['skill'] or not SAFE_ID.fullmatch(s['skill']) or s['primary'] not in s['outputs']):
            errors.append(s['id'] + ': skill and primary output required')
        if s['type']=='skill' and s['validator'] in {'scope_review','evidence_review','presentation_review'}:
            errors.append(s['id'] + ': review policies require real checkpoints')
        if s['type']=='checkpoint' and s['validator'] not in {'scope_review','evidence_review','presentation_review'}:
            errors.append(s['id'] + ': unknown checkpoint policy')
        if s['type']=='checkpoint' and (s['skill'] or s['outputs'] or s['primary']):
            errors.append(s['id'] + ': checkpoints cannot execute skills or produce knowledge')
        if 'gates' in s and set(s['gates']) != set(mandatory_gates(s)):
            errors.append(s['id'] + ': gates must match the mandatory checks for this producer')
        if s['validator']=='language_review':
            required={'draft','glossary','scenario','validation','manifest'}
            allowed=required|{'manifest','technical-flow','business-rules','glossary-increment'}
            if not required<=set(s['inputs']) or not set(s['inputs'])<=allowed:
                errors.append(s['id'] + ': Language Reviewer requires bounded draft/glossary/Scenario/Validation inputs')
            if (s['type']!='skill' or s['scope']!='item' or s['primary']!='final-document' or
                    s['outputs']!={'final-document':'markdown','language-review':'language-review'}):
                errors.append(s['id'] + ': Language Reviewer requires final-document and language-review bundle')
        if s['validator'] in {'confluence_plan','confluence_render'}:
            required={'document','manifest','language-review'}
            if s['validator']=='confluence_render': required|={'presentation-plan','presentation-metadata'}
            outputs=({'presentation-plan':'confluence-presentation-plan','presentation-metadata':'confluence-presentation-metadata'}
                     if s['validator']=='confluence_plan' else {'confluence-body':'storage-xhtml','publisher-metadata':'confluence-render'})
            primary='presentation-plan' if s['validator']=='confluence_plan' else 'confluence-body'
            if (set(s['inputs'])!=required or s['outputs']!=outputs or s['primary']!=primary
                    or s['type']!='skill' or s['scope']!='item'):
                errors.append(s['id']+': bounded Confluence presentation contract required')
        if s['validator']=='presentation_review' and (s['scope']!='item' or set(s['inputs'])!={'presentation-plan','presentation-metadata'}):
            errors.append(s['id']+': presentation review requires plan and metadata')
        if s['scope']=='run' and any(specs.get(d,{}).get('scope')=='item' for d in s['depends_on']):
            errors.append(s['id'] + ': run stage cannot depend on a per-Scenario stage')
        for selector in s['inputs'].values():
            if selector in {'request','baseline.glossary'} or selector.startswith('base.'):
                if selector!='request' and s['scope']!='item':
                    errors.append(s['id'] + ': scoped/baseline selector requires an item stage')
                continue
            owner,key = selector.split('.',1) if '.' in selector else ('','')
            if owner not in seen or key not in specs[owner]['outputs'] or owner not in s['depends_on']:
                errors.append(s['id'] + ': undeclared dependency/input ' + selector)
        seen.add(s['id'])
    domains = [s for s in specs.values() if s['validator']=='domain' and s['scope']=='run']
    reviews = [s for s in specs.values() if s['validator']=='scope_review']
    if len(domains)!=1 or len(reviews)!=1 or domains[0]['type']!='skill' or reviews[0]['type']!='checkpoint' or reviews[0]['scope']!='run' or domains[0]['id'] not in reviews[0]['depends_on']:
        errors.append('pipeline: exactly one Domain producer and mandatory scope checkpoint required')
    elif any(s['scope']=='item' and reviews[0]['id'] not in ancestors(config,s['id']) for s in specs.values()):
        errors.append('pipeline: every item stage must depend on scope approval')
    evidence=[s for s in specs.values() if s['validator']=='evidence_review']
    validators=[s for s in specs.values() if s['validator']=='validation']
    if len(evidence)!=1 or len(validators)!=1 or evidence[0]['scope']!='item' or evidence[0]['type']!='checkpoint' or validators[0]['id'] not in evidence[0]['depends_on']:
        errors.append('pipeline: Validator and conditional evidence checkpoint required')
    elif any(s['validator'] in {'glossary','documentation','language_review','confluence_plan','confluence_render'} and evidence[0]['id'] not in ancestors(config,s['id']) for s in specs.values()):
        errors.append('pipeline: glossary/documentation/language review must depend on evidence review')
    for renderer in (s for s in specs.values() if s['validator']=='confluence_render'):
        checkpoints=[s for s in specs.values() if s['validator']=='presentation_review' and s['id'] in ancestors(config,renderer['id'])]
        if len(checkpoints)!=1:
            errors.append(renderer['id']+': exactly one ancestor presentation approval required')
        else:
            checkpoint=checkpoints[0]
            if any(renderer['inputs'].get(name)!=checkpoint['inputs'].get(name) for name in ('presentation-plan','presentation-metadata')):
                errors.append(renderer['id']+': renderer must consume the approved plan/metadata')
    return errors


def ancestors(config, stage):
    specs={s['id']:s for s in config['stages']}
    result=set()
    def visit(key):
        for dep in specs[key]['depends_on']:
            if dep in specs and dep not in result:
                result.add(dep);visit(dep)
    visit(stage)
    return result


def new_node(spec, item, dependencies):
    return dict(spec_id=spec['id'], item_id=item, active=True, dependencies=dependencies,
                status='PENDING', input_fingerprints={}, bundle={}, attempts=[], correction_ids=[], approval_id=None)


def compile_nodes(state):
    specs = {s['id']:s for s in state['pipeline']['stages']}
    wanted = {}
    for spec in specs.values():
        if spec['scope']=='run':
            wanted[spec['id']]=new_node(spec,None,list(spec['depends_on']))
    previous_glossary = None
    for item in state['work_items']:
        for spec in specs.values():
            if spec['scope']!='item':
                continue
            key=spec['id']+'@'+item['id']
            deps=[d if specs[d]['scope']=='run' else d+'@'+item['id'] for d in spec['depends_on']]
            if 'baseline.glossary' in spec['inputs'].values() and previous_glossary:
                deps.append(previous_glossary)
            wanted[key]=new_node(spec,item['id'],deps)
            if spec['validator']=='glossary':
                previous_glossary=key
    for key,node in state['nodes'].items():
        node['active']=key in wanted
    for key,node in wanted.items():
        if key in state['nodes']:
            state['nodes'][key].update(active=True,dependencies=node['dependencies'])
        else:
            state['nodes'][key]=node


class Run:
    def __init__(self, directory):
        self.root=Path(directory).resolve()
        self.state=load(self.root/'run.yaml')
        self._state_hash=digest(self.state)
        self._validated=set()
        self._read_cache={}
        require(schema_errors('documentation-run',self.state))
        require(pipeline_errors(self.state['pipeline']))

    @classmethod
    def create(cls, parent, request, *, run_id=None, pipeline=None, glossary=None):
        request=copy.deepcopy(request.get('documentation_request',request))
        require(schema_errors('documentation-request',request))
        config=copy.deepcopy(pipeline or load(DEFAULT_PIPELINE))
        require(pipeline_errors(config))
        day=datetime.now(timezone(timedelta(hours=3))).strftime('%Y%m%d')
        run_id=run_id or f'osago-{day}-{uuid.uuid4().hex[:8]}'
        if not SAFE_ID.fullmatch(run_id):
            raise ValueError('invalid run_id')
        root=safe_path(parent,run_id)
        root.mkdir(parents=True,exist_ok=False)
        (root/'inputs').mkdir()
        save_data(root/'inputs/documentation-request.yaml',request)
        current=load(glossary) if glossary is not None else empty_glossary()
        require(glossary_errors(current))
        save_data(root/'inputs/glossary-baseline.yaml',current)
        state=dict(schema_version='1.0',run_id=run_id,status='IN_PROGRESS',created_at=now(),updated_at=now(),
                   request=binding(root,root/'inputs/documentation-request.yaml','documentation-request'),
                   glossary_baseline=binding(root,root/'inputs/glossary-baseline.yaml','glossary'),
                   pipeline=config,work_items=[],nodes={},reviews=[],results={})
        compile_nodes(state)
        require(schema_errors('documentation-run',state))
        save_data(root/'run.yaml',state)
        return cls(root)

    def spec(self,node):
        return next(s for s in self.state['pipeline']['stages'] if s['id']==node['spec_id'])

    def inputs(self,key):
        node=self.state['nodes'][key];spec=self.spec(node)
        item=next((i for i in self.state['work_items'] if i['id']==node['item_id']),None)
        result={}
        for name,selector in spec['inputs'].items():
            if selector=='request':
                ref=self.state['request']
            elif selector=='baseline.glossary':
                ref=self.state['glossary_baseline']
                pos=self.state['work_items'].index(item)
                if pos:
                    previous=self.state['work_items'][pos-1]['id']
                    producer=next(n for n in self.state['nodes'].values() if n['active'] and n['item_id']==previous and self.spec(n)['validator']=='glossary')
                    ref=producer['bundle']['glossary']
            else:
                owner,field=selector.split('.',1)
                if owner=='base':
                    ref=item['artifacts'][field]
                else:
                    producer=self.state['nodes'][owner if self._spec_by_id(owner)['scope']=='run' else owner+'@'+node['item_id']]
                    ref=producer['bundle'][field]
            result[name]=ref
        return result

    def _spec_by_id(self,key):
        return next(s for s in self.state['pipeline']['stages'] if s['id']==key)

    def persist(self):
        self.state['updated_at']=now()
        require(schema_errors('documentation-run',self.state))
        # OS file locking releases on process exit; a leftover lock file cannot block resume.
        with (self.root/'run.lock').open('a+b') as lock:
            if lock.tell()==0:
                lock.write(b'0');lock.flush()
            lock.seek(0)
            try:
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            except OSError as exc:
                raise StateChangedError('run state is being updated by another agent') from exc
            try:
                if digest(load(self.root/'run.yaml'))!=self._state_hash:
                    raise StateChangedError('run state changed in another session; reload before continuing')
                save_data(self.root/'run.yaml',self.state)
                self._state_hash=digest(self.state)
            finally:
                lock.seek(0)
                if os.name=='nt': msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
                else: fcntl.flock(lock.fileno(),fcntl.LOCK_UN)

    def invalidate(self,key, *, include_self=False):
        changed={key}
        while True:
            more={k for k,n in self.state['nodes'].items() if n['active'] and set(n['dependencies']) & changed}
            if more <= changed:
                break
            changed |= more
        for k in changed if include_self else changed-{key}:
            node=self.state['nodes'][k]
            if node['status']=='RUNNING':
                raise ValueError('cannot invalidate a running stage; record failure first')
            node.update(status='STALE',approval_id=None)
        for event in self.state['reviews']:
            if event['node_id'] in changed and event['status']=='ACCEPTED':
                event['status']='STALE'
        self.state['results']={}
        self.state['status']='IN_PROGRESS'

    def _reconcile(self):
        for key,node in self.state['nodes'].items():
            if not node['active'] or node['status'] not in {'COMPLETED','SKIPPED','WAITING_FOR_REVIEW'}:
                continue
            try:
                refs=self.inputs(key)
                for ref in refs.values(): self._read(ref)
                fingerprints={name:r['content_hash'] for name,r in refs.items()}
                if node['input_fingerprints']!=fingerprints:
                    self.invalidate(key,include_self=True)
                    continue
                for ref in node['bundle'].values():
                    self._read(ref)
                if self.spec(node)['validator']=='domain':
                    for item in self.state['work_items']:
                        for ref in item['artifacts'].values():
                            self._read(ref)
                driver=self.spec(node)['validator']
                if driver=='confluence_plan' and node['bundle']:
                    from confluence_render import check_assets
                    ref=node['bundle']['presentation-metadata']
                    check_assets(self._read(ref),safe_path(self.root,ref['path']).parent)
                if driver=='confluence_render' and node['bundle']:
                    self._check_render_attachments(node['bundle'])
                if driver=='presentation_review':
                    ref=refs['presentation-metadata']
                    from confluence_render import check_assets
                    check_assets(self._read(ref),safe_path(self.root,ref['path']).parent)
                    if node['status']=='COMPLETED': self._checkpoint_approval(key)
                if node['status']=='COMPLETED' and self.spec(node)['type']=='skill':
                    stamp=digest([key,node['bundle'],refs])
                    if stamp not in self._validated:
                        self._validate(key,node['bundle'],refs)
                        self._validated.add(stamp)
            except PipelineGateError as exc:
                self.invalidate(key)
                node['status']='FAILED'
                node['attempts'][-1].update(status='FAILED',finished_at=now(),
                    error=dict(type='PipelineGateError',message=str(exc),timestamp=now()))
                self.state['status']='FAILED'
            except (ValueError,KeyError,OSError,yaml.YAMLError):
                self.invalidate(key,include_self=True)

    def plan(self):
        self._read_cache={}
        self._reconcile()
        active=[(k,n) for k,n in self.state['nodes'].items() if n['active']]
        for key,node in active:
            if node['status']=='FAILED':
                self.state['status']='FAILED';self.persist()
                return dict(action='FAILED',run_id=self.state['run_id'],node_id=key,error=node['attempts'][-1]['error'])
            if node['status']=='RUNNING':
                self.state['status']='IN_PROGRESS';self.persist()
                spec=self.spec(node);attempt=node['attempts'][-1]
                refs=self.inputs(key)
                extra=self._presentation_task(key,refs)
                return dict(**extra,action='RUNNING',run_id=self.state['run_id'],node_id=key,
                            skill=spec['skill'],skill_path=resolve_skill_path(spec['skill']),
                            inputs={name:str(safe_path(self.root,r['path'])) for name,r in self.inputs(key).items()},
                            outputs=spec['outputs'],output_dir=str(safe_path(self.root,attempt['directory'])),attempt=attempt['number'],
                            message='Resume the recorded attempt, or explicitly fail/retry it; never invoke twice.')
        for key,node in active:
            if node['status'] in {'COMPLETED','SKIPPED'}:
                continue
            if any(self.state['nodes'][d]['status'] not in {'COMPLETED','SKIPPED'} for d in node['dependencies']):
                continue
            refs=self.inputs(key)
            for ref in refs.values():
                self._read(ref)
            spec=self.spec(node)
            if spec['type']=='checkpoint':
                view=self.checkpoint_view(key,refs)
                node['input_fingerprints']={k:r['content_hash'] for k,r in refs.items()}
                if spec['validator']=='evidence_review' and not view['items']:
                    node['status']='SKIPPED';continue
                node['status']='WAITING_FOR_REVIEW';self.state['status']='WAITING_FOR_USER';self.persist()
                return dict(action='WAITING_FOR_USER',run_id=self.state['run_id'],node_id=key,review=view)
            self.state['status']='IN_PROGRESS';self.persist()
            extra=self._presentation_task(key,refs)
            return dict(**extra,action='EXECUTE_SKILL',run_id=self.state['run_id'],node_id=key,skill=spec['skill'],
                        skill_path=resolve_skill_path(spec['skill']),
                        inputs={k:str(safe_path(self.root,r['path'])) for k,r in refs.items()},
                        outputs=spec['outputs'],corrections=[r for r in self.state['reviews'] if r['id'] in node['correction_ids'] and r['status']=='PENDING'],
                        previous_outputs={k:str(safe_path(self.root,r['path'])) for k,r in node['bundle'].items()})
        if all(n['status'] in {'COMPLETED','SKIPPED'} for _,n in active) and self.state['work_items']:
            self.state['status']='COMPLETED'
            self.state['results']={item['id']:self._item_results(item) for item in self.state['work_items']}
            domain=next(n for n in self.state['nodes'].values() if n['active'] and self.spec(n)['validator']=='domain')
            self.persist();return dict(action='COMPLETED',run_id=self.state['run_id'],run=str(self.root),
                                       domain_map=domain['bundle']['domain-tree'],results=self.state['results'])
        raise ValueError('workflow blocked by invalid/missing dependency; no speculative execution')

    def _item_results(self,item):
        result={}
        for node in self.state['nodes'].values():
            if node['active'] and node['item_id']==item['id'] and self.spec(node)['type']=='skill':
                for name in self.spec(node)['outputs']:
                    result[name]=node['bundle'][name]
        if 'final-document' in result:
            if 'documentation' in result:
                result['draft-document']=result['documentation']
            result['documentation']=result['final-document']
        return result

    def start(self,key):
        plan=self.plan()
        if plan.get('action')!='EXECUTE_SKILL' or plan['node_id']!=key:
            raise ValueError('stage is not next/ready; dependencies or human review not satisfied')
        node=self.state['nodes'][key]
        number=len(node['attempts'])+1
        relative=f'stages/{key}/attempt-{number:04d}'
        safe_path(self.root,relative).mkdir(parents=True,exist_ok=False)
        node['input_fingerprints']={k:r['content_hash'] for k,r in self.inputs(key).items()}
        node['attempts'].append(dict(number=number,directory=relative,started_at=now(),finished_at=None,
                                    status='RUNNING',error=None,artifacts={}))
        node['status']='RUNNING';self.persist()
        if not Path(plan['skill_path']).is_file():
            message='configured skill is unavailable: '+plan['skill']
            self.fail(key,'SkillUnavailable',message)
            raise ValueError(message)
        plan['output_dir']=str(safe_path(self.root,relative));plan['attempt']=number
        return plan

    def fail(self,key,error_type,message):
        node=self.state['nodes'][key]
        if node['status']!='RUNNING':
            raise ValueError('failure belongs to a running attempt')
        attempt=node['attempts'][-1]
        attempt.update(status='FAILED',finished_at=now(),error=dict(type=error_type,message=message,timestamp=now()))
        node['status']='FAILED';self.state['status']='FAILED';self.persist()

    def _read(self,ref):
        # Cache only within one synchronous operation; every resume/finish rechecks disk.
        key=(ref['path'],ref['content_hash'],ref['schema'])
        if key not in self._read_cache:
            self._read_cache[key]=read_binding(self.root,ref)[1]
        return self._read_cache[key]

    def _load_refs(self,refs):
        return {key:self._read(ref) for key,ref in refs.items() if ref['schema']}

    def _presentation_task(self,key,refs):
        driver=self.spec(self.state['nodes'][key])['validator']
        if driver not in {'confluence_plan','confluence_render'}: return {}
        extra={'presentation_mode':'plan' if driver=='confluence_plan' else 'render'}
        if driver=='confluence_render': extra['hierarchy_approval']=self._presentation_approval(key,refs)
        return extra

    def _presentation_approval(self,key,refs):
        candidates=[(k,n) for k,n in self.state['nodes'].items() if k in self._ancestors(key)
                    and self.spec(n)['validator']=='presentation_review']
        if len(candidates)!=1: raise ValueError('presentation approval checkpoint required')
        checkpoint,node=candidates[0]
        current=self.inputs(checkpoint)
        if any(refs[name]!=current[name] for name in current):
            raise ValueError('renderer must consume the current approved presentation inputs')
        return self._checkpoint_approval(checkpoint)

    def _checkpoint_approval(self,key):
        node=self.state['nodes'][key]
        fingerprints={name:ref['content_hash'] for name,ref in self.inputs(key).items()}
        events=[r for r in self.state['reviews'] if r['id']==node['approval_id']]
        if (node['status']!='COMPLETED' or len(events)!=1 or events[0]['decision']!='APPROVE'
                or events[0]['status']!='ACCEPTED' or events[0]['node_id']!=key
                or events[0]['input_fingerprints']!=fingerprints or node['input_fingerprints']!=fingerprints):
            raise ValueError('current explicit hierarchy approval required')
        return copy.deepcopy(events[0])

    def _check_render_attachments(self,bundle):
        metadata=self._read(bundle['publisher-metadata'])
        directory=safe_path(self.root,bundle['publisher-metadata']['path']).parent
        for attachment in metadata['attachments']:
            path=safe_path(directory,attachment['bundle_path'])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=attachment['content_hash']:
                raise ValueError('accepted presentation attachment missing/changed')

    def _validate(self,key,bundle,refs):
        spec=self.spec(self.state['nodes'][key]);driver=spec['validator']
        data=self._load_refs(bundle)
        for gate in effective_gates(spec):
            inputs=self._load_refs(refs)
            document=draft=context=None
            if gate=='document-structure':
                document=safe_path(self.root,bundle['documentation']['path']).read_bytes().decode('utf-8')
            elif gate=='final-invariants':
                document=safe_path(self.root,bundle['final-document']['path']).read_bytes().decode('utf-8')
                draft=safe_path(self.root,refs['draft']['path']).read_bytes().decode('utf-8')
                owners=[ancestor for ancestor in self._ancestors(key)
                        if self.spec(self.state['nodes'][ancestor])['validator']=='documentation']
                if len(owners)!=1:
                    raise PipelineGateError('[final-invariants/COMPOSER_CONTEXT] exactly one accepted Composer ancestor required')
                context=self._load_refs(self.inputs(owners[0]))
            run_gate(gate,data,inputs,document=document,draft=draft,context=context)
        if driver in {'domain','artifact'}:
            k=data['knowledge'];kind=spec['primary']
            if k.get('model_profile')!=PROFILE:
                raise ValueError('stage outputs require existing scoped-knowledge-v1')
            kwargs={name:data[artifact] for artifact,name in VALIDATE_INPUTS.items() if artifact!=kind and artifact in data}
            previous=load(safe_path(self.root,refs['knowledge']['path'])) if 'knowledge' in refs else None
            require(validate(kind,data[kind],k,previous_knowledge=previous,**kwargs))
            for name,ref in refs.items():
                if name in bundle and name not in {'knowledge',kind,'documentation-request'}:
                    if projection(load(safe_path(self.root,ref['path'])))!=projection(data[name]):
                        raise ValueError('upstream projection changed beyond terminology/revision: '+name)
        elif driver=='validation':
            inputs=self._load_refs(refs)
            require(check_report(data['validation-report'],data['gaps'],inputs))
            if data['validation-report']['mechanical_errors'] or data['validation-report']['summary']['review_status']!='complete':
                raise ValueError('Validator must finish semantic claim review; audit draft alone is not a completed stage')
        elif driver=='glossary':
            require(glossary_errors(data['glossary']))
            increment=data['glossary-increment'];base=load(safe_path(self.root,refs['glossary']['path']))
            if merge(base,increment)!=data['glossary']:
                raise ValueError('glossary increment does not reproduce result')
            for name,ref in refs.items():
                if name not in {'glossary'} and increment['input_hashes'].get(name)!=ref['content_hash']:
                    raise ValueError('glossary increment input hash mismatch: '+name)
        elif driver in {'confluence_plan','confluence_render'}:
            from confluence_render import make_plan,approve,render,check_assets
            inputs=self._load_refs(refs)
            document=safe_path(self.root,refs['document']['path']).read_bytes().decode('utf-8')
            if driver=='confluence_plan':
                candidate=data['presentation-plan']
                expected=make_plan(document,inputs['manifest'],inputs['language-review'],technical_expand=candidate['technical_expand'])
                if candidate!=expected: raise ValueError('presentation plan must match reviewed inputs and wait for human agreement')
                ref=bundle['presentation-metadata']
                check_assets(data['presentation-metadata'],safe_path(self.root,ref['path']).parent)
            else:
                self._presentation_approval(key,refs)
                ref=refs['presentation-metadata'];asset_root=safe_path(self.root,ref['path']).parent
                check_assets(inputs['presentation-metadata'],asset_root)
                metadata=data['publisher-metadata']
                body,expected,assets=render(document,inputs['manifest'],approve(inputs['presentation-plan']),
                    review=inputs['language-review'],metadata=inputs['presentation-metadata'],asset_root=asset_root)
                actual=safe_path(self.root,bundle['confluence-body']['path']).read_bytes().decode('utf-8')
                if body!=actual or metadata!=expected: raise ValueError('Confluence representation/metadata differs from approved inputs')
                if metadata['publisher']['body_file']!=safe_path(self.root,bundle['confluence-body']['path']).name:
                    raise ValueError('publisher body_file must name the accepted XHTML')
                if safe_path(self.root,bundle['confluence-body']['path']).parent!=safe_path(self.root,bundle['publisher-metadata']['path']).parent:
                    raise ValueError('Confluence body and publisher metadata must share a bundle directory')
                self._check_render_attachments(bundle)
        elif driver=='language_review':
            from language_review import check_review
            inputs=self._load_refs(refs)
            draft=safe_path(self.root,refs['draft']['path']).read_bytes().decode('utf-8')
            final=safe_path(self.root,bundle['final-document']['path']).read_bytes().decode('utf-8')
            review=data['language-review']
            require(check_review(draft,final,review,inputs['glossary'],inputs['scenario'],inputs['validation'],
                                 technical_flow=inputs.get('technical-flow'),business_rules=inputs.get('business-rules'),
                                 glossary_increment=inputs.get('glossary-increment'),manifest=inputs.get('manifest')))
            if review['review']['status']!='COMPLETED':
                raise ValueError('Language Reviewer must complete language and semantic checks before run completion')
        elif driver=='documentation':
            inputs=self._load_refs(refs)
            report,gaps,glossary=inputs.pop('report'),inputs.pop('gaps'),inputs.pop('glossary')
            require(check_report(report,gaps,inputs,allow_omitted_inputs={'source-map','scenario-definition'}))
            require(glossary_errors(glossary))
            manifest=data['documentation-manifest']
            expected=dict(report_hash=digest(report),gaps_hash=digest(gaps),report_ref=report['id'],
                          package_ref=inputs['scenario']['package_ref'],scope_ref=inputs['scenario']['scope_ref'],
                          claim_ids=report['claim_inventory'],publication_gate=report['summary']['publication_gate'],inputs=report['inputs'])
            if any(manifest.get(k)!=v for k,v in expected.items()) or manifest.get('document_profile')!='reviewed-draft-v1':
                raise ValueError('documentation provenance does not match validated inputs')
            document=safe_path(self.root,bundle['documentation']['path']).read_bytes()
            if hashlib.sha256(document).hexdigest()!=manifest['document_hash'] or data['documentation-meta']!=manifest:
                raise ValueError('documentation bytes/metadata hash mismatch')
            if manifest['document']['glossary']!=dict(id=glossary['id'],revision=glossary['revision'],content_hash=digest(glossary)):
                raise ValueError('documentation glossary provenance mismatch')
            metadata=manifest['document'];k=inputs['knowledge']
            if metadata['scenario_id']!=inputs['scenario']['scenario_id'] or metadata['source_revision']!=k['scope']['revisions'] or metadata['domain_ids']!=sorted(e['id'] for e in k['entities'] if e['type']=='Domain'):
                raise ValueError('documentation scope metadata mismatch')
            provenance=dict(inputs, **{'validation-report':report,'validation-gaps':gaps,'glossary':glossary})
            if 'provenance' in metadata and metadata['provenance']!=provenance:
                raise ValueError('documentation structured provenance does not match validated inputs')
            indexes={name:records(artifact) for name,artifact in provenance.items()}
            known=set(records(list(provenance.values())))
            # Source Map is intentionally omitted from Composer inputs. Its entry IDs
            # survive as validated source_ids in the supplied projections.
            for index in indexes.values():
                for row in index.values(): known.update(row.get('source_ids',[]))
            for block in metadata['blocks']:
                if not set(block['derived_from'])<=known:
                    raise ValueError('documentation block contains dangling provenance reference: '+
                                     ', '.join(sorted(set(block['derived_from'])-known)))
                for field in block['source_fields']:
                    row=indexes.get(field['artifact'],{}).get(field['record'])
                    if row is None or field['field'] not in row:
                        raise ValueError('documentation block source field does not exist')
            if not set(metadata['unresolved'])<=known:
                raise ValueError('documentation contains dangling unresolved reference')
            if any(b['end_line']>len(document.splitlines()) or b['start_line']>b['end_line'] for b in manifest['document']['blocks']):
                raise ValueError('invalid documentation block spans')
            if report['summary']['review_status']!='complete' or report['mechanical_errors']:
                raise ValueError('documentation requires completed valid claim review')

    def finish(self,key,result):
        self._read_cache={}
        node=self.state['nodes'][key]
        if node['status']!='RUNNING':
            raise ValueError('finish belongs to a running attempt')
        try:
            require(schema_errors('documentation-stage-result',result))
            spec=self.spec(node);attempt=node['attempts'][-1];directory=safe_path(self.root,attempt['directory'])
            if set(result['artifacts'])!=set(spec['outputs']):
                raise ValueError('stage must return exactly its declared artifact bundle')
            bundle={name:binding(self.root,safe_path(directory,path),None if schema in {'markdown','storage-xhtml'} else schema)
                    for name,path in result['artifacts'].items() for schema in [spec['outputs'][name]]}
            refs=self.inputs(key)
            if {k:content_hash(safe_path(self.root,r['path']),r['schema']) for k,r in refs.items()}!=node['input_fingerprints']:
                raise ValueError('inputs changed during execution; retry with current inputs')
            self._validate(key,bundle,refs)
            pending=[r for r in self.state['reviews'] if r['id'] in node['correction_ids'] and r['status']=='PENDING']
            if set(result.get('applied_review_ids',[]))!={r['id'] for r in pending}:
                raise ValueError('pending human corrections must be explicitly applied by the owning skill')
            correction_fields=({spec['primary']} if bundle[spec['primary']]['schema'] else
                               {name for name,ref in bundle.items() if ref['schema']})
            correction_fields |= {'knowledge'} if 'knowledge' in bundle else set()
            if pending and node['bundle'] and all(
                correction_hash(safe_path(self.root,bundle[name]['path']))==
                correction_hash(safe_path(self.root,node['bundle'][name]['path'])) for name in correction_fields):
                raise ValueError('human correction did not change its structured artifact')
            if 'knowledge' in node['bundle'] and spec['validator']=='artifact':
                previous_package=load(safe_path(self.root,node['bundle']['knowledge']['path']))
                current_package=load(safe_path(self.root,bundle['knowledge']['path']))
                # A newly approved Domain revision owns a scope change. _validate above
                # still requires the output scope to equal its actual upstream input.
                # Preserve all other continuity checks against the previous attempt.
                if previous_package['scope']!=current_package['scope']:
                    item=next((i for i in self.state['work_items'] if i['id']==node['item_id']),None)
                    if item and self.state['nodes']['scope-review']['status']=='COMPLETED':
                        domain_package=self._read(item['artifacts']['knowledge'])
                        if (domain_package['package_id']==current_package['package_id'] and
                                domain_package['scope']==current_package['scope']):
                            previous_package=copy.deepcopy(previous_package)
                            previous_package['scope']=copy.deepcopy(domain_package['scope'])
                require(increment_errors(previous_package,current_package))
            items=None
            if spec['validator']=='domain':
                items=self._accept_items(result.get('work_items',[]),directory,bundle)
            elif result.get('work_items'):
                raise ValueError('only Domain Decomposer defines work items')
            changed={k:r['content_hash'] for k,r in bundle.items()}!={k:r['content_hash'] for k,r in node['bundle'].items()}
            if changed and node['bundle']:
                self.invalidate(key)
            node.update(bundle=bundle,status='COMPLETED')
            self._validated.add(digest([key,bundle,refs]))
            attempt.update(status='COMPLETED',finished_at=now(),artifacts=copy.deepcopy(bundle))
            for review in pending:
                review.update(status='APPLIED',applied_artifacts=copy.deepcopy(bundle))
            if items is not None:
                self.state['work_items']=items;compile_nodes(self.state)
            self.state['status']='IN_PROGRESS';self.persist()
        except StateChangedError:
            raise
        except (ValueError,KeyError,OSError,TypeError,yaml.YAMLError) as exc:
            spec=self.spec(node)
            message=f"{key} ({spec['skill']}), gates={','.join(effective_gates(spec)) or 'schema'}: {exc}"
            self.fail(key,'PipelineGateError' if isinstance(exc,PipelineGateError) else 'ContractError',message)
            return dict(action='FAILED',node_id=key,error=message)
        return dict(action='ACCEPTED',node_id=key)

    def _accept_items(self,items,directory,bundle):
        if not items:
            raise ValueError('Domain producer must prepare all scoped atomic Scenario packages')
        root_k=load(safe_path(self.root,bundle['knowledge']['path']))
        root_entities={e['id']:e for e in root_k['entities']}
        accepted=[];package_ids={root_k['package_id']};ids=set();scenarios=set()
        for item in items:
            if not SAFE_ID.fullmatch(item['id']) or item['id'] in ids:
                raise ValueError('work item requires unique safe workflow ID')
            ids.add(item['id'])
            if set(item['artifacts'])!={'knowledge','domain-tree','scenario-definition'}:
                raise ValueError('each Scenario requires Domain-owned knowledge/tree/definition')
            refs={k:binding(self.root,safe_path(directory,p),SCHEMA_ALIASES.get(k,k)) for k,p in item['artifacts'].items()}
            data=self._load_refs(refs);k=data['knowledge']
            require(validate('domain-tree',data['domain-tree'],k,scenario_definition=data['scenario-definition']))
            require(validate('scenario-definition',data['scenario-definition'],k,domain_tree=data['domain-tree']))
            if k.get('model_profile')!=PROFILE or k['package_id'] in package_ids:
                raise ValueError('Scenario packages require distinct stable package IDs; never fork one KB revision')
            package_ids.add(k['package_id'])
            if item['scenario_id']!=data['scenario-definition']['scenario_id'] or not any(e['id']==item['domain_id'] and e['type']=='Domain' for e in k['entities']):
                raise ValueError('work item must reference existing Domain/Scenario IDs')
            if item['scenario_id'] in scenarios or k['scope']['scenarios']!=[item['scenario_id']]:
                raise ValueError('work items must have unique, individually scoped Scenario IDs')
            scenarios.add(item['scenario_id'])
            entities={e['id']:e for e in k['entities']}
            for eid in (item['domain_id'],item['scenario_id']):
                if eid not in root_entities or any(entities[eid][field]!=root_entities[eid][field] for field in ('type','identity_key')):
                    raise ValueError('master/work item Entity identities disagree: '+eid)
            accepted.append(dict(item,artifacts=refs))
        if {i['scenario_id'] for i in accepted}!=set(root_k['scope']['scenarios']):
            raise ValueError('work items must cover every scoped Scenario; Domain producer must resolve decomposition')
        return accepted

    def checkpoint_view(self,key,refs):
        data=self._load_refs(refs);spec=self.spec(self.state['nodes'][key])
        if spec['validator']=='scope_review':
            tree,k=data['domain-tree'],data['knowledge']
            return dict(domain=load(safe_path(self.root,self.state['request']['path']))['domain'],
                        scenarios=[dict(id=n['id'],name=n['name'],goal=n['business_goal']) for n in tree['nodes'] if n['type']=='scenario'],
                        capabilities=[dict(id=n['id'],name=n['name']) for n in tree['nodes'] if n['type']=='capability'],
                        out_of_scope=k['scope']['exclusions'],ambiguous_boundaries=k['scope']['unresolved_constraints'],
                        questions=[g['question'] for g in k['gaps'] if g['status']=='open'])
        if spec['validator']=='presentation_review':
            plan=data['presentation-plan'];metadata=data['presentation-metadata']
            from confluence_render import check_assets
            check_assets(metadata,safe_path(self.root,refs['presentation-metadata']['path']).parent)
            return dict(kind='CONFLUENCE_HIERARCHY',headings=plan['headings'],technical_expand=plan['technical_expand'],
                        plan_hash=plan['plan_hash'],policy=plan['policy'],diagrams=list(metadata.get('diagrams',{})),
                        message='Approve this reviewed document hierarchy and presentation only; no Confluence publication.')
        report,gaps=data['validation-report'],data['gaps']
        items=[]
        for row in report['claim_reviews']:
            if row['status']!='CONFIRMED':
                items.append(dict(kind=row['status'],id=row['claim_id'],question=row['reason'],action=row['required_action']))
        items += [dict(kind=g['reason'],id=g['id'],question=g['question'],action=g['next_action']) for g in gaps['gaps'] if g['status']=='open']
        items += [dict(kind=f['kind'],id=f['id'],question=f['reason'],action=f['required_action']) for f in report['findings'] if f['status']=='open' and f['blocking']]
        items += [dict(kind=c['status'],id=c['id'],question=c['reason'],action=c['required_action']) for c in report['comparisons'] if c['status'] in {'CONFLICT','UNRESOLVED'}]
        items += [dict(kind='LIMITATION',id='limitation:'+str(i),question=v,action='review') for i,v in enumerate(report['limitations'])]
        items += [dict(kind=r['result'],id=r['confirmation_ref'],question=r['reason'],action='review') for r in report.get('runtime_reviews',[]) if not r['reviewed'] and r['result']!='NOT_REQUIRED']
        return dict(items=items)

    def review(self,key,decision,response, *, target=None):
        plan=self.plan()
        if plan.get('action')!='WAITING_FOR_USER' or plan['node_id']!=key:
            raise ValueError('no current human checkpoint for this decision')
        if decision not in {'APPROVE','CORRECT'} or not response.strip():
            raise ValueError('explicit human response/decision required')
        node=self.state['nodes'][key]
        if decision=='CORRECT':
            if target is None or target not in self.state['nodes'] or not self.state['nodes'][target]['active'] or self.spec(self.state['nodes'][target])['type']!='skill':
                raise ValueError('correction requires the owning skill stage, not orchestrator reasoning')
            if target not in self._ancestors(key):
                raise ValueError('correction target must own an upstream artifact of this checkpoint')
        event=dict(id='review:'+uuid.uuid4().hex,node_id=key,decision=decision,response=response,timestamp=now(),
                   input_fingerprints=copy.deepcopy(node['input_fingerprints']),target_node=target,
                   status='ACCEPTED' if decision=='APPROVE' else 'PENDING',applied_artifacts={})
        self.state['reviews'].append(event)
        if decision=='APPROVE':
            node.update(status='COMPLETED',approval_id=event['id'])
        else:
            self.invalidate(target,include_self=True)
            self.state['nodes'][target]['status']='PENDING'
            self.state['nodes'][target]['correction_ids'].append(event['id'])
        self.state['status']='IN_PROGRESS';self.persist()

    def _ancestors(self,key):
        result=set()
        def visit(k):
            for d in self.state['nodes'][k]['dependencies']:
                if d not in result:
                    result.add(d);visit(d)
        visit(key);return result

    def retry(self,key):
        node=self.state['nodes'][key]
        if node['status'] not in {'FAILED','STALE'}:
            raise ValueError('retry applies only to failed/stale stages')
        node['status']='PENDING';self.state['status']='IN_PROGRESS';self.persist()

    def rerun_from(self,key):
        if key not in self.state['nodes'] or not self.state['nodes'][key]['active'] or self.spec(self.state['nodes'][key])['type']!='skill':
            raise ValueError('rerun requires an active skill stage')
        self.invalidate(key,include_self=True)
        self.state['nodes'][key]['status']='PENDING';self.persist()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['init','resume','start','finish','fail','review','retry','rerun'])
    p.add_argument('--run',type=Path);p.add_argument('--runs-dir',type=Path,default=ROOT/'runs')
    p.add_argument('--domain');p.add_argument('--request',type=Path);p.add_argument('--run-id')
    p.add_argument('--pipeline',type=Path);p.add_argument('--glossary',type=Path)
    p.add_argument('--node');p.add_argument('--result',type=Path)
    p.add_argument('--decision',choices=['APPROVE','CORRECT']);p.add_argument('--response');p.add_argument('--target')
    p.add_argument('--error-type',default='SkillFailure');p.add_argument('--message')
    args=p.parse_args()
    try:
        if args.action=='init':
            request=load(args.request) if args.request else {'domain':args.domain}
            run=Run.create(args.runs_dir,request,run_id=args.run_id,pipeline=load(args.pipeline) if args.pipeline else None,glossary=args.glossary)
            result=dict(run=str(run.root),**run.plan())
        else:
            if args.run is None:
                raise ValueError('--run required')
            run=Run(args.run)
            if args.action=='start': result=run.start(args.node)
            elif args.action=='finish': result=run.finish(args.node,load(args.result))
            elif args.action=='fail': run.fail(args.node,args.error_type,args.message or 'Skill failed.');result=run.plan()
            elif args.action=='review': run.review(args.node,args.decision,args.response or '',target=args.target);result=run.plan()
            elif args.action=='retry': run.retry(args.node);result=run.plan()
            elif args.action=='rerun': run.rerun_from(args.node);result=run.plan()
            else: result=run.plan()
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError,TypeError,yaml.YAMLError) as exc:
        p.exit(2,str(exc)+'\n')


if __name__=='__main__':
    main()
