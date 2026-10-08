"""Offline reviewed Markdown -> verified Confluence DC storage; no publication."""
import argparse
import copy
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
import yaml
from validate import load, schema_errors

ROOT = Path(__file__).resolve().parents[2]
from paths import skill_resource

PROFILE = skill_resource('osago-confluence-renderer', 'references', 'confluence-profile.yaml')
MD = MarkdownIt('commonmark', {'html': False}).enable('table')
AC, RI = 'http://atlassian.com/content', 'http://atlassian.com/resource/identifier'
INTERNAL = re.compile(r'\b(?:entity|claim|evidence|snapshot|scenario-step|technical-step|domain|scope|kb|rule|actor|integration|comparison|finding|gap):[\w:./-]+')
LOCAL = re.compile(r'(?<![\w])(?:[A-Za-z]:[\\/]|\\\\)[^\s<>"\x60]+|(?<![\w:/])(?:\.?\.?/)?(?:sources|runs|tools|\.codex|\.cursor|\.probe|\.tmp)/[^\s<>"\x60]+|(?<![\w:/])/(?:home|tmp|mnt|Users|workspace)/[^\s<>"\x60]+')

class RenderError(ValueError):
    pass

def sha(value):
    return hashlib.sha256(value.encode('utf8') if isinstance(value, str) else value).hexdigest()

def digest(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')))

def tree(document):
    return SyntaxTreeNode(MD.parse(document))

def plain(node):
    if node.type in {'text', 'code_inline'}:
        return node.content
    if node.type in {'softbreak', 'hardbreak'}:
        return ' '
    return ''.join(plain(c) for c in node.children)

def headings(document):
    result = [{'level': int(n.tag[1:]), 'text': plain(n), 'line': n.map[0]+1}
              for n in tree(document).children if n.type == 'heading']
    if not result or result[0]['level'] != 1 or sum(h['level'] == 1 for h in result) != 1:
        raise RenderError('Exactly one document H1 is required.')
    previous = 1
    for item in result:
        if item['level'] > previous + 1:
            raise RenderError('Heading level jumps require hierarchy review.')
        previous = item['level']
    return result

def binding(document, manifest, review=None):
    errors = schema_errors('documentation-manifest', manifest)
    if errors:
        raise RenderError('; '.join(errors))
    if review is not None:
        errors = schema_errors('language-review', review)
        if errors:
            raise RenderError('; '.join(errors))
        if (review['review']['status'] != 'COMPLETED' or review['final_hash'] != sha(document)
            or review['inputs']['draft_hash'] != manifest['document_hash']
            or review['inputs'].get('manifest_hash') != digest(manifest)
            or review['publication_gate'] != manifest['publication_gate']
            or review['claim_ids'] != manifest['claim_ids']):
            raise RenderError('Review/final/manifest provenance does not match.')
        blocks = review['blocks']
    else:
        if manifest['document_hash'] != sha(document):
            raise RenderError('Provide language-review report when final differs from Composer manifest.')
        blocks = manifest.get('document', {}).get('blocks', [])
    if not blocks or any(b['start_line'] > b['end_line'] or b['end_line'] > len(document.splitlines()) for b in blocks):
        raise RenderError('Complete line provenance is required.')
    return blocks

def make_plan(document, manifest, review=None, *, technical_expand=False):
    binding(document, manifest, review)
    payload = dict(document_hash=sha(document), manifest_hash=digest(manifest),
        language_review_hash=digest(review) if review else None,
        headings=headings(document), technical_expand=technical_expand,
        policy='preserve-source-hierarchy-and-order-v1')
    return dict(schema_version='1.0', **payload, plan_hash=digest(payload),
                approval=dict(status='WAITING_FOR_REVIEW', approved_plan_hash=None))

def approve(plan):
    """Caller needs direct human agreement on this concrete hierarchy."""
    result = copy.deepcopy(plan)
    result['approval'] = dict(status='COMPLETED', approved_plan_hash=result['plan_hash'])
    return result

def macro(name, body, title=None):
    param = '<ac:parameter ac:name="title">'+html.escape(title)+'</ac:parameter>' if title else ''
    return ('<ac:structured-macro ac:name="'+name+'" ac:schema-version="1">'+param+
            '<ac:rich-text-body>'+body+'</ac:rich-text-body></ac:structured-macro>')

def check_storage(body):
    try:
        root = ET.fromstring('<root xmlns:ac="'+AC+'" xmlns:ri="'+RI+'">'+body+'</root>')
    except ET.ParseError as error:
        raise RenderError('Invalid storage XML: '+str(error)) from error
    visible = ' '.join(root.itertext())
    if INTERNAL.search(body) or LOCAL.search(body):
        raise RenderError('Private ID/path leaked into body.')
    if re.search(r'(?m)^\s*#{1,6}\s|\x60\x60\x60|\[!WARNING\]|\[!NOTE\]|\[[^\]]+\]\([^)]+\)', visible):
        raise RenderError('Unrendered Markdown in body.')
    for element in root.iter():
        if element.tag == '{'+AC+'}structured-macro' and element.get('{'+AC+'}name') not in {'info','warning','expand'}:
            raise RenderError('Unverified macro.')
        if element.tag == 'a' and urlsplit(element.get('href','')).scheme not in {'https','http'}:
            raise RenderError('Unresolved/unsafe link.')
    return root

class Renderer:
    def __init__(self, manifest, blocks, metadata, asset_root, mermaid_cli):
        self.metadata, self.asset_root = metadata or {}, Path(asset_root).resolve()
        self.mermaid_cli = mermaid_cli
        self.private, self.attachments, self.assets = [], [], {}
        self.ids = set(manifest['claim_ids'])
        self.ids.update(manifest.get('document',{}).get('unresolved',[]))
        for b in blocks:
            self.ids.update(b['derived_from'])
            self.ids.update(f['record'] for f in b['source_fields'])
        identifiers = self.metadata.get('inline_identifiers',[])
        self.code_identifiers=set(identifiers)
        self.code_pattern = re.compile('|'.join(re.escape(s) for s in sorted(identifiers,key=len,reverse=True))) if identifiers else None

    def hide(self, match, kind):
        self.private.append(dict(kind=kind,original=match.group()))
        return ''

    def clean(self, value):
        for identifier in sorted(self.ids,key=len,reverse=True):
            # CodeComponent IDs can be literal symbols; never delete code spelling.
            if ':' not in identifier or identifier in self.code_identifiers:
                continue
            value = re.sub(r'(?<![\w:-])'+re.escape(identifier)+r'(?![\w:-])',
                           lambda m:self.hide(m,'internal-reference'),value)
        value = INTERNAL.sub(lambda m:self.hide(m,'internal-reference'),value)
        return LOCAL.sub(lambda m:self.hide(m,'local-reference'),value)

    def text(self, value):
        value = self.clean(value)
        pattern = re.compile(r'\b(?:PARTIALLY_CONFIRMED|CONFIRMED|INFERRED|UNKNOWN|CONFLICT)\b|\b(?:GET|POST|PUT|PATCH|DELETE)\s+/[\w/{}.?=&%-]+')
        spans = [(m.start(),m.start()+len(m.group().rstrip('.,;'))) for m in pattern.finditer(value)]
        if self.code_pattern:
            spans += [(m.start(),m.end()) for m in self.code_pattern.finditer(value)
                      if (m.start()==0 or not value[m.start()-1].isalnum())
                      and (m.end()==len(value) or not value[m.end()].isalnum())]
        output,end = [],0
        for start,stop in sorted(spans):
            if start < end:
                continue
            output += [html.escape(value[end:start]),'<code>'+html.escape(value[start:stop])+'</code>']
            end = stop
        return ''.join(output)+html.escape(value[end:])

    def local_asset(self, reference):
        path = (self.asset_root/reference).resolve()
        if not path.is_relative_to(self.asset_root) or not path.is_file():
            raise RenderError('Diagram asset is missing/outside selected directory.')
        return path

    def image(self, node):
        source = node.attrGet('src')
        spec = self.metadata.get('diagrams',{}).get(source)
        if not spec:
            raise RenderError('Image needs explicit attachment metadata.')
        caption = spec.get('caption') or plain(node)
        path = self.local_asset(spec.get('source_file',source))
        if path.suffix.lower() == '.mmd':
            if spec.get('rendered_file'):
                data = self.local_asset(spec['rendered_file']).read_bytes()
            else:
                executable = self.mermaid_cli or shutil.which('mmdc')
                if not executable:
                    raise RenderError('Mermaid needs prepared PNG or local mmdc; no raw .mmd publication.')
                with tempfile.TemporaryDirectory() as directory:
                    output = Path(directory)/'diagram.png'
                    subprocess.run([executable,'-i',str(path),'-o',str(output)],check=True,
                                   timeout=60,capture_output=True)
                    data = output.read_bytes()
        else:
            data = path.read_bytes()
        if (len(data)<33 or not data.startswith(b'\x89PNG\r\n\x1a\n') or data[12:16]!=b'IHDR'
            or not all(struct.unpack('>II',data[16:24])) or b'IEND' not in data):
            raise RenderError('Diagram must be a valid PNG.')
        if '.mmd' in caption:
            raise RenderError('Human-readable diagram caption required.')
        name = 'diagram-'+sha(data)[:16]+'.png'
        self.assets[name] = data
        if not any(a['filename']==name for a in self.attachments):
            self.attachments.append(dict(filename=name,media_type='image/png',content_hash=sha(data),
                bundle_path='attachments/'+name,caption=self.clean(caption),source_ref=source,source_hash=sha(path.read_bytes())))
        self.private.append(dict(kind='diagram',original=source))
        return '<ac:image ac:alt="'+html.escape(self.clean(caption),quote=True)+'"><ri:attachment ri:filename="'+name+'" /></ac:image>'

    def link(self, node):
        href,label = node.attrGet('href'),plain(node)
        mapped = self.metadata.get('links',{}).get(href)
        if mapped:
            href,label = mapped['url'],mapped['title']
        if INTERNAL.search(label) or href.startswith('#') or LOCAL.search(href) or not urlsplit(href).scheme:
            self.private.append(dict(kind='link',original=dict(href=href,label=label)))
            return self.text(label) if not INTERNAL.search(label) and label not in self.ids else ''
        if urlsplit(href).scheme not in {'https','http'} or INTERNAL.search(href) or LOCAL.search(href):
            raise RenderError('Unsafe/private public link.')
        if label==href or re.match(r'https?://',label):
            raise RenderError('URL link requires supplied human-readable title.')
        return '<a href="'+html.escape(href,quote=True)+'">'+self.text(label)+'</a>'

    def node(self, node, rules=False):
        kind = node.type
        if kind=='inline':
            groups=[[]]; separators=[]
            for child in node.children:
                if child.type in {'softbreak','hardbreak'}:
                    groups.append([])
                    separators.append(' ' if child.type=='softbreak' else '<br />')
                else:
                    groups[-1].append(child)
            visible=[]
            for index,group in enumerate(groups):
                original=''.join(plain(child) for child in group)
                label=re.match(r'^(?:Внутренняя трассировка|Локальный путь):\s*',original)
                if label:
                    tail=self.clean(original[label.end():])
                    if not re.sub(r'[\s;:,.]+','',tail):
                        self.private.append(dict(kind='private-metadata-line',original=original))
                        continue
                if visible: visible.append(separators[index-1])
                visible.append(''.join(self.node(child,rules) for child in group))
            return ''.join(visible)
        if kind in {'td','th','heading'} and INTERNAL.search(plain(node)):
            remaining=self.clean(plain(node))
            if not re.sub(r'[\s;:,.]+','',remaining):
                raise RenderError('A substantive heading/table cell has only a private ID: needs reviewed human label.')
        if kind=='text':
            return self.text(node.content)
        if kind=='code_inline':
            return '<code>'+html.escape(self.clean(node.content))+'</code>'
        if kind=='link':
            return self.link(node)
        if kind=='image':
            return self.image(node)
        if kind in {'softbreak','hardbreak'}:
            return ' ' if kind=='softbreak' else '<br />'
        if kind=='blockquote':
            match = re.match(r'^\[!(WARNING|CAUTION|NOTE|TIP|IMPORTANT)\]\s*',plain(node))
            body = ''.join(self.node(c,rules) for c in node.children)
            if match:
                body = body.replace(html.escape(match.group().strip()),'',1)
                return macro('warning' if match[1] in {'WARNING','CAUTION','IMPORTANT'} else 'info',body)
            return '<blockquote>'+body+'</blockquote>'
        if kind in {'fence','code_block'}:
            if node.info.strip().lower() in {'mermaid','storage','xhtml','html'} or self.clean(node.content)!=node.content:
                raise RenderError('Raw storage/diagram/private code block requires upstream presentation metadata.')
            return '<pre><code>'+html.escape(node.content)+'</code></pre>'
        if kind=='hr':
            return '<hr />'
        body = ''.join(self.node(c,rules) for c in node.children)
        if kind in {'root','inline'}:
            return body
        if rules and kind=='bullet_list' and all(re.match(r'^(?:Правило|Условие|При выполнении|При невыполнении|Причина|Шаги|Статус):',plain(c)) for c in node.children):
            return ''.join(self.node(field,False) for item in node.children for field in item.children)
        tags = dict(heading=node.tag,paragraph='p',strong='strong',em='em',bullet_list='ul',
                    ordered_list='ol',list_item='li',table='table',thead='thead',tbody='tbody',
                    tr='tr',th='th',td='td')
        if kind not in tags:
            raise RenderError('Unsupported node: '+kind)
        if kind=='paragraph' and '<ac:image' not in body and not re.sub(r'<[^>]+>','',body).strip():
            return ''
        attr = ' start="'+str(int(node.attrGet('start')))+'"' if kind=='ordered_list' and node.attrGet('start') else ''
        return '<'+tags[kind]+attr+'>'+body+'</'+tags[kind]+'>'

def render(document, manifest, plan, *, review=None, metadata=None, asset_root='.', profile=None, mermaid_cli=None):
    blocks = binding(document,manifest,review)
    profile = profile or load(PROFILE)
    if profile['representation']!='storage' or profile['api_path']!='/rest/api':
        raise RenderError('Only verified DC storage profile supported.')
    expected = approve(make_plan(document,manifest,review,technical_expand=plan['technical_expand']))
    if plan!=expected:
        raise RenderError('Approve current concrete hierarchy before rendering.')
    renderer = Renderer(manifest,blocks,metadata,asset_root,mermaid_cli)
    output,pending,section = [],[],None
    def flush():
        if not pending:
            return
        body = ''.join(pending)
        if section=='technical' and plan['technical_expand']:
            body = macro('expand',body,'Технические подробности')
        output.append(body)
        pending.clear()
    for node in tree(document).children:
        if node.type=='heading' and node.tag in {'h1','h2'}:
            flush()
            line = node.map[0]+1
            matches = [b['section'] for b in blocks if b['start_line']<=line<=b['end_line']]
            if not matches:
                raise RenderError('Heading has no manifest section provenance.')
            section = matches[0]
            output.append(renderer.node(node))
            continue
        if re.match(r'^(?:Comparison|Finding|Gap|Evidence|Claim|Source):\s*[\[{]',plain(node)):
            raise RenderError('Artifact dump is not reviewed prose; request an upstream human-readable block.')
        value = renderer.node(node,rules=section=='business-rules')
        if section=='gaps' and node.type!='blockquote' and value:
            value = macro('warning',value)
        if node.type=='paragraph' and 'Publication gate:' in plain(node):
            value = macro('warning' if manifest['publication_gate']=='blocked' else 'info',value)
        pending.append(value)
    flush()
    body = '\n'.join(output)
    check_storage(body)
    meta = dict(schema_version='1.0',status='COMPLETED',
        inputs=dict(document_hash=sha(document),manifest_hash=digest(manifest),
            language_review_hash=digest(review) if review else None,presentation_metadata_hash=digest(metadata or {})),
        hierarchy_plan=plan,profile=profile,
        publisher=dict(body_file='10-confluence-body.storage.xhtml',content_format='storage',
            representation='storage',api_path='/rest/api',body_hash=sha(body),
            publication_gate=manifest['publication_gate'],eligible=manifest['publication_gate']=='passed',
            attachment_order='ensure-page-then-upload-before-final-body'),
        attachments=renderer.attachments,
        traceability=dict(claim_ids=manifest['claim_ids'],blocks=blocks,hidden_references=renderer.private),
        checks=dict(storage_xml=True,private_references_in_body=0,raw_markdown_in_body=0))
    errors = schema_errors('confluence-render',meta)
    if errors:
        raise RenderError('; '.join(errors))
    return body,meta,renderer.assets

def snapshot_assets(metadata, asset_root):
    """Bind selected presentation files, without reading any system source."""
    metadata=copy.deepcopy(metadata or {})
    root=Path(asset_root).resolve()
    hashes={}
    for item in metadata.get('diagrams',{}).values():
        for field in ('source_file','rendered_file'):
            if field in item:
                path=(root/item[field]).resolve()
                if not path.is_relative_to(root) or not path.is_file():
                    raise RenderError('Selected presentation asset is missing/outside its directory.')
                hashes[item[field]]=sha(path.read_bytes())
    metadata['asset_hashes']=hashes
    errors=schema_errors('confluence-presentation-metadata',metadata)
    if errors: raise RenderError('; '.join(errors))
    return metadata


def check_assets(metadata, asset_root):
    if snapshot_assets(metadata,asset_root)!=metadata:
        raise RenderError('Presentation assets changed since the plan was accepted.')


def write_bundle(directory, body, metadata, assets, overwrite=False):
    directory = Path(directory)
    files = {'10-confluence-body.storage.xhtml':body.encode('utf8'),
             '10-publisher-metadata.yaml':yaml.safe_dump(metadata,allow_unicode=True,sort_keys=False).encode('utf8')}
    files.update({'attachments/'+name:data for name,data in assets.items()})
    if not overwrite and any((directory/name).exists() for name in files):
        raise RenderError('Existing bundle requires explicit --overwrite.')
    for name,data in files.items():
        path = directory/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['plan','approve','render','check'])
    for name in ('document','manifest','language-review','metadata','plan','output-dir','mermaid-cli'):
        parser.add_argument('--'+name,required=name=='plan')
    parser.add_argument('--asset-root',default='.')
    for name in ('technical-expand','human-agreement','overwrite'):
        parser.add_argument('--'+name,action='store_true')
    args = parser.parse_args()
    try:
        if args.mode=='approve':
            if not args.human_agreement:
                raise RenderError('Direct human hierarchy agreement required.')
            Path(args.plan).write_text(yaml.safe_dump(approve(load(args.plan)),allow_unicode=True,sort_keys=False),encoding='utf8')
            return 0
        if not args.document or not args.manifest:
            raise RenderError('Reviewed document and manifest required.')
        document = Path(args.document).read_bytes().decode('utf8')
        manifest = load(args.manifest)
        review = load(args.language_review) if args.language_review else None
        if args.mode=='plan':
            if Path(args.plan).exists() and not args.overwrite:
                raise RenderError('Existing plan requires --overwrite.')
            plan = make_plan(document,manifest,review,technical_expand=args.technical_expand)
            if args.output_dir:
                output=Path(args.output_dir);output.mkdir(parents=True,exist_ok=True)
                sidecar=output/'presentation-metadata.yaml'
                if sidecar.exists() and not args.overwrite: raise RenderError('Existing presentation metadata requires --overwrite.')
                metadata=snapshot_assets(load(args.metadata) if args.metadata else {},args.asset_root)
                sidecar.write_text(yaml.safe_dump(metadata,allow_unicode=True,sort_keys=False),encoding='utf8')
            Path(args.plan).parent.mkdir(parents=True,exist_ok=True)
            Path(args.plan).write_text(yaml.safe_dump(plan,allow_unicode=True,sort_keys=False),encoding='utf8')
            return 0
        if not args.output_dir:
            raise RenderError('--output-dir required.')
        body,meta,assets = render(document,manifest,load(args.plan),review=review,
            metadata=load(args.metadata) if args.metadata else None,asset_root=args.asset_root,
            mermaid_cli=args.mermaid_cli)
        if args.mode=='check':
            directory = Path(args.output_dir)
            if ((directory/'10-confluence-body.storage.xhtml').read_bytes()!=body.encode('utf8')
                or load(directory/'10-publisher-metadata.yaml')!=meta
                or any((directory/'attachments'/name).read_bytes()!=data for name,data in assets.items())):
                raise RenderError('Bundle differs from rendering of approved inputs.')
        else:
            write_bundle(args.output_dir,body,meta,assets,args.overwrite)
        print('COMPLETED; representation=storage; publication_gate='+manifest['publication_gate'])
        return 0
    except (RenderError,OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        print('FAILED: '+str(error),file=sys.stderr)
        return 1

if __name__=='__main__':
    sys.exit(main())
