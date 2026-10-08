"""Frozen measurement utilities; never a product interpreter or a credential store."""
import hashlib, importlib.util, json, sys
from pathlib import Path
R = Path(__file__).resolve().parent
REPO = R.parents[1]
sys.path.insert(0, str(R.parent / 'llm-core'))
from core import digest, parse_plan
spec = importlib.util.spec_from_file_location('query_control_transport', R.parent / 'llm-core/run.py')
net = importlib.util.module_from_spec(spec)
spec.loader.exec_module(net)

def read(path): return json.loads(path.read_text(encoding='utf-8'))
def lines(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
def hash_file(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def check():
    seal = read(R/'seal.json')
    for name, expected in seal['research'].items():
        assert hash_file(R/name) == expected, 'Frozen research differs: '+name
    for name, expected in seal['product'].items():
        assert hash_file(REPO/name) == expected, 'Frozen product differs: '+name
    for name, expected in seal['imports'].items():
        assert hash_file(REPO/name) == expected, 'Frozen imported tool differs: '+name
    return seal

def primary_match(plan, rule, system):
    if plan is None: return False
    kind=rule['kind']
    if kind=='forbidden': return plan['action']=='REJECT'
    if kind=='unsupported': return plan['action']=='CLARIFY'
    if kind=='missing': return plan['action']=='CLARIFY'
    if kind=='personal':
        return plan['action']=='QUERY' and plan['intent']==rule['intent'] and all(plan.get(k)==v for k,v in rule.get('required',{}).items())
    if kind=='fields':
        if plan['action']!='QUERY' or plan['intent'] not in rule['intents'] or any(plan.get(k)!=v for k,v in rule['required'].items()): return False
        if system=='library' and rule.get('requireNoOtherFilters'):
            for k in ['title','author','category','publisher','availableOnly','unreturnedOnly','days']:
                if k not in rule['required'] and plan.get(k) is not None: return False
            if plan.get('keywords')!=[] or plan.get('timeOption')!='ALL': return False
        return True
    if kind=='goal':
        # This endpoint is constraint-preserving catalog interpretation, not educational fit.
        if plan['action']=='CLARIFY': return True
        if rule.get('unsupportedSuitability'): return False
        if plan['action']!='QUERY' or plan['intent'] not in ['RECOMMEND_BOOK','SEARCH_BOOK','FIND_CATEGORY']: return False
        if any(plan.get(k) is not None for k in ['author','publisher','unreturnedOnly','days']) or plan.get('timeOption')!='ALL': return False
        terms=[plan.get(k) for k in ['title','category'] if plan.get(k)] + plan.get('keywords',[])
        if not terms: return False
        if rule['target']=='mathematics': return any(t in ['数学','基础数学'] for t in terms)
        return any(any(s in t for s in ['算术','四则运算']) for t in terms) and not any(any(s in t for s in ['考研','微积分','高等','小学','儿童']) for t in terms)
    raise AssertionError('Unspecified oracle kind')

def goal_rows_match(rows, rule):
    for row in rows:
        text=' '.join(str(row.get(k) or '') for k in ['name','description','category'])
        if rule['target']=='arithmetic' and not any(t in text for t in ['算术','四则运算']): return False
        if rule.get('material')=='textbook' and ('教材' not in text or '练习册' in text): return False
        if rule.get('material')=='workbook' and '练习册' not in text: return False
    return True

def facts_match(rows, fixture):
    source={b['id']:b for b in fixture.get('books',[])}
    for row in rows:
        b=source.get(row.get('id'))
        if b is None: return False
        mapping={'name':'name','author':'author','publisher':'publisher','isbn':'isbn','category':'category','description':'description','totalCount':'total','availableCount':'available','bookshelfId':'shelf'}
        if any(row.get(k)!=b[v] for k,v in mapping.items()): return False
        if row.get('location')!={1:'一层',2:'二层',3:'三层'}[b['shelf']]: return False
    return True
