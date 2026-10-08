import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stats import joint,conditioned,conditional_permutation,entropy,family_bootstrap
class StatisticsBoundaries(unittest.TestCase):
 def test_difficulty_mixture_is_not_within_case_excess(self):
  cases={'easy':[(False,False)]*4,'hard':[(True,True)]*4}
  self.assertEqual(joint(sum(cases.values(),[]))['excess'],.25)
  self.assertEqual(conditioned(cases),0)
 def test_pairing_changes_joint_not_margins(self):
  self.assertEqual(joint([(True,True),(False,False)])['excess'],.25)
  self.assertEqual(joint([(True,False),(False,True)])['excess'],-.25)
 def test_constant_errors_have_no_permutation_variation(self):
  r=conditional_permutation({'hard':[(True,True)]*4},100)
  self.assertEqual(r['observedExcess'],0);self.assertEqual(r['oneSidedExploratoryP'],1)
 def test_uniform_wrong_consensus_has_zero_entropy(self):
  self.assertEqual(entropy(['WRONG']*4),0);self.assertEqual(entropy(['RIGHT','WRONG']),1)
 def test_family_constant_resampling_preserves_effect(self):
  r=family_bootstrap({'a':[(True,True),(False,False)]},{'a':'same'},100)
  self.assertEqual(r['low'],.25);self.assertEqual(r['high'],.25)
if __name__=='__main__':unittest.main()
