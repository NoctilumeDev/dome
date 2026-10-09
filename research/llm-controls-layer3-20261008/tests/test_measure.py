import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from measure import identifiable
class MinimumVariation(unittest.TestCase):
 def test_constant_is_unidentified(self):
  cc={str(i):[(False,True)]*8 for i in range(8)};self.assertFalse(identifiable(cc,{k:int(k)%2 for k in cc}))
 def test_one_model_varies_is_insufficient(self):
  cc={str(i):[(False,j%2==0) for j in range(8)] for i in range(8)};self.assertFalse(identifiable(cc,{k:int(k)%2 for k in cc}))
 def test_clusters_not_calls(self):
  cc={str(i):[(j%2==0,j%3==0) for j in range(8)] for i in range(4)};self.assertTrue(identifiable(cc,{k:int(k)%2 for k in cc}));self.assertFalse(identifiable(cc,{k:0 for k in cc}))
if __name__=='__main__':unittest.main()
