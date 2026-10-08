import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from analyze import handling_correct,outcome_status

class ActualOutcomes(unittest.TestCase):
 def test_original_native_rejection_cannot_be_rescued_by_good_proposal(self):
  self.assertFalse(handling_correct(True,False,True,'REJECT',{'action':'CLARIFY'}))
  self.assertTrue(handling_correct(True,False,True,'CLARIFY',{'action':'CLARIFY'}))
 def test_entry_gate_applies_before_every_policy(self):
  first={'nativePlannerCalled':False,'response':{'status':'REJECT'}}
  selected={'response':{'status':'QUERY'}}
  for group in ('A:a','B','C:a','D','E:a','F4:a'):
   self.assertEqual(outcome_status(group,{'action':'QUERY'},selected,first)[0],'REJECT')
 def test_abstention_is_not_native_completion(self):
  first={'nativePlannerCalled':True,'response':{'status':'QUERY'}}
  status,_,origin=outcome_status('B',None,None,first)
  self.assertEqual(status,'POLICY_ABSTENTION')
  self.assertFalse(handling_correct(False,True,False,status,None))
  self.assertTrue(handling_correct(False,False,True,status,None))
  self.assertIn('OFFLINE',origin)
 def test_unavailable_and_scope_pending_are_distinct(self):
  p={'action':'QUERY'}
  self.assertFalse(handling_correct(True,True,False,'CLARIFY',p))
  self.assertTrue(handling_correct(True,True,False,'CONFIRM_SCOPE',p))
  self.assertFalse(handling_correct(True,True,False,'REJECT',p))

if __name__=='__main__':unittest.main()
