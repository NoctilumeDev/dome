"""Configure unchanged semantic scorers for new identity views; no answer repairs."""
import argparse,importlib.util,pathlib,sys,types
from collect import R,REPO,check,read,write
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser();p.add_argument('suite');a=p.parse_args();check()
 core=REPO/'research/llm-core';sys.path.insert(0,str(core))
 if a.suite in ['core','extension','counterexamples']:
  m=load('final_unchanged_analyze',core/'analyze.py');m.ROOT=R/'views'/a.suite;sys.argv=['analyze','core'];m.main()
 elif a.suite in ['formal','external','tier','time-day0','time-day1']:
  sys.path.insert(0,str(REPO/'research/llm-counterexamples-20261008'));m=load('final_unchanged_measure',REPO/'research/llm-controls-layer3-20261008/measure.py');m.R=R/'views/layer3';m.main()
 elif a.suite.startswith('query-'):
  view=R/'views'/('query-day1' if a.suite.endswith('day1') else 'query-day0')
  original=REPO/'research/llm-query-controls-20261008'
  common=load('common',original/'common.py');common.R=view;common.REPO=REPO;common.check=check
  if 'review' in a.suite:
   sys.modules['review_collect']=types.SimpleNamespace(review_check=check)
   m=load('final_unchanged_review_measure',original/'review_measure.py')
  else:m=load('final_unchanged_measure_v2',original/'measure_v2.py')
  m.main()
 else:return
 write(R/'scoring'/f'{a.suite}.json',dict(status='COMPLETE',semanticScorerUnchanged=True,identityProjectionOnly=True,notIndependentExternalValidation=True,legacyNarrativeAndCostScopesNotPromoted=True))
 print('SCORING_PASS '+a.suite,flush=True)
if __name__=='__main__':main()
