"""Finite experiment decisions; no Chinese intent classifier and no SQL executor."""
import hashlib
import json
from collections import Counter

Q_FIELDS = frozenset('action intent entity category timeOption reason'.split())
B_FIELDS = frozenset('action intent title author category publisher keywords availableOnly unreturnedOnly timeOption days limit reason'.split())

def _object(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError('DUPLICATE_FIELD')
        result[k] = v
    return result

def parse_plan(system, text):
    # Book production accepts exactly this code-fence representation; Qingye does not.
    text = text.strip()
    if system == 'library' and text.startswith('```json\n') and text.endswith('```'):
        text = text[8:-3].strip()
    try:
        p = json.loads(text, object_pairs_hook=_object)
    except (ValueError, TypeError):
        return None, 'INVALID_JSON'
    fields = Q_FIELDS if system == 'qingye' else B_FIELDS
    if not isinstance(p, dict) or set(p) != fields:
        return None, 'INVALID_FIELDS'
    if p['action'] not in ('QUERY', 'CLARIFY', 'REJECT'):
        return None, 'INVALID_ACTION'
    if system == 'qingye':
        if any(v is not None and not isinstance(v, str) for v in p.values()):
            return None, 'INVALID_TYPES'
    else:
        for f in ('action', 'intent', 'title', 'author', 'category', 'publisher', 'timeOption', 'reason'):
            if p[f] is not None and not isinstance(p[f], str):
                return None, 'INVALID_TYPES'
        if not isinstance(p['keywords'], list) or any(not isinstance(v, str) for v in p['keywords']):
            return None, 'INVALID_TYPES'
        for f in ('availableOnly', 'unreturnedOnly'):
            if p[f] is not None and type(p[f]) is not bool:
                return None, 'INVALID_TYPES'
        if type(p['limit']) is not int or not 1 <= p['limit'] <= 50:
            return None, 'INVALID_LIMIT'
        if p['days'] is not None and (type(p['days']) is not int or not 1 <= p['days'] <= 30):
            return None, 'INVALID_DAYS'
    return p, 'STRUCTURE_VALID'

def canonical(p):
    return json.dumps(p, ensure_ascii=False, sort_keys=True, separators=(',', ':')) if p is not None else None

def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()

def review(raw):
    try:
        r = json.loads(raw, object_pairs_hook=_object)
        if not isinstance(r, dict) or set(r) != {'decision', 'reason'}:
            return 'INVALID_REVIEW'
        if r['decision'] not in ('ACCEPT', 'CLARIFY', 'REJECT') or not isinstance(r['reason'], str) or len(r['reason']) > 240:
            return 'INVALID_REVIEW'
        return r['decision']
    except (ValueError, TypeError):
        return 'INVALID_REVIEW'

def choose_majority(proposals, n):
    good = [p for p in proposals[:n] if p is not None]
    counts = Counter(canonical(p) for p in good)
    if not counts:
        return None
    key, count = counts.most_common(1)[0]
    return json.loads(key) if count > n / 2 else None

def decisions(pa, pb, reviews, pools):
    eq = pa is not None and pb is not None and canonical(pa) == canonical(pb)
    result = {'A:a': pa, 'A:b': pb, 'B': pa if eq else None}
    result['C:a'] = pa if eq and reviews.get('b:a') == 'ACCEPT' else None
    result['C:b'] = pb if eq and reviews.get('a:b') == 'ACCEPT' else None
    result['D'] = pa if eq and all(reviews.get(k) == 'ACCEPT' for k in ('b:a', 'a:b')) else None
    result['E:a'] = pa if pa is not None and reviews.get('a:a') == 'ACCEPT' else None
    result['E:b'] = pb if pb is not None and reviews.get('b:b') == 'ACCEPT' else None
    for model, plans in pools.items():
        for n in (2, 3, 4):
            result[f'F{n}:{model}'] = choose_majority(plans, n)
    return result

def score_plan(plan, oracle):
    if plan is None:
        return {'proposal_correct': False, 'decision': 'CLARIFY', 'execution_candidate': False}
    matches = any(all(plan.get(k) == v for k, v in allowed.items()) for allowed in oracle['allowed'])
    return {'proposal_correct': matches, 'decision': plan['action'], 'execution_candidate': plan['action'] == 'QUERY'}

def clean_response(body):
    # Preserve final content, metadata and usage; never retain hidden chain of thought.
    body = json.loads(json.dumps(body))
    for choice in body.get('choices', []):
        message = choice.get('message', {})
        for key in ('reasoning_content', 'reasoning', 'analysis'):
            message.pop(key, None)
    return body
