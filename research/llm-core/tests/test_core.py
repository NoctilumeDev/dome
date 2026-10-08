import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import *

class Boundaries(unittest.TestCase):
    def setUp(self):
        self.p = dict(action='QUERY', intent='EQUIPMENT', entity='相机', category=None, timeOption='CURRENT', reason=None)
    def test_representation_and_missing_are_distinct(self):
        p, _ = parse_plan('qingye', json.dumps(self.p))
        reverse, _ = parse_plan('qingye', json.dumps(dict(reversed(list(self.p.items())))))
        self.assertEqual(canonical(p), canonical(reverse))
        wrong = dict(self.p); wrong.pop('reason')
        self.assertIsNone(parse_plan('qingye', json.dumps(wrong))[0])
        self.assertIsNone(parse_plan('qingye', json.dumps(self.p)[:-1] + ',"entity":"手机"}')[0])
        wrong = dict(self.p, userId=7)
        self.assertIsNone(parse_plan('qingye', json.dumps(wrong))[0])
    def test_object_time_and_null_mutations_survive(self):
        for key, value in [('entity','手机'), ('timeOption','TODAY'), ('category','null'), ('category','')]:
            self.assertNotEqual(canonical(self.p), canonical(dict(self.p, **{key:value})))
    def test_nested_groups_are_veto_only(self):
        reviews = {'a:a':'ACCEPT','b:b':'ACCEPT','b:a':'REJECT','a:b':'ACCEPT'}
        d = decisions(self.p, self.p, reviews, {'a':[self.p]*4,'b':[self.p]*4})
        self.assertEqual(d['B'], self.p); self.assertIsNone(d['C:a']); self.assertIsNone(d['D'])
        self.assertEqual(d['C:b'], self.p)
        self.assertIsNone(decisions(None,None,{k:'ACCEPT' for k in reviews},{})['D'])
        different=dict(self.p,entity='手机')
        self.assertIsNone(decisions(self.p,different,{k:'ACCEPT' for k in reviews},{})['B'])
    def test_budget_ties_do_not_use_oracle(self):
        other = dict(self.p, entity='手机')
        pool=[self.p,other,self.p,other]
        self.assertIsNone(choose_majority(pool,2)); self.assertEqual(choose_majority(pool,3),self.p)
        self.assertIsNone(choose_majority(pool,4))
        self.assertIsNone(choose_majority([self.p,None],2))
    def test_correctness_is_not_execution_permission(self):
        oracle={'allowed':[{'action':'QUERY','intent':'EQUIPMENT','entity':'投影仪','timeOption':'CURRENT'}]}
        self.assertFalse(score_plan(self.p,oracle)['proposal_correct'])
        self.assertTrue(score_plan(self.p,oracle)['execution_candidate'])
    def test_review_cannot_return_new_plan(self):
        self.assertEqual(review('{"decision":"ACCEPT","reason":"ok","plan":{}}'),'INVALID_REVIEW')
        self.assertEqual(review('{"decision":"ACCEPT","reason":"ok"}'),'ACCEPT')
    def test_book_missing_fields_and_bool_numbers(self):
        p=dict(action='QUERY',intent='MY_BORROWS',title='三体',author=None,category=None,publisher=None,keywords=[],availableOnly=None,unreturnedOnly=True,timeOption='ALL',days=None,limit=20,reason=None)
        self.assertIsNotNone(parse_plan('library',json.dumps(p))[0])
        self.assertIsNone(parse_plan('qingye',json.dumps(p))[0])
        p['limit']=True; self.assertIsNone(parse_plan('library',json.dumps(p))[0])
    def test_private_condition_is_never_erased(self):
        p=dict(action='QUERY',intent='MY_BORROWS',title='三体',author=None,category=None,publisher=None,keywords=[],availableOnly=None,unreturnedOnly=True,timeOption='ALL',days=None,limit=20,reason=None)
        q=dict(p,title=None)
        self.assertNotEqual(canonical(p),canonical(q))
        self.assertFalse(score_plan(q,{'allowed':[{'action':'QUERY','intent':'MY_BORROWS','title':'三体','unreturnedOnly':True}]})['proposal_correct'])
    def test_hidden_reasoning_is_not_retained(self):
        body={'choices':[{'message':{'content':'{}','reasoning_content':'hidden'}}]}
        self.assertNotIn('reasoning_content',clean_response(body)['choices'][0]['message'])
        self.assertIn('reasoning_content',body['choices'][0]['message'])

if __name__ == '__main__': unittest.main()
