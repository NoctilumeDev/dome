import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from measure_v2 import requested_book_ids

class RequestedSetMappingTest(unittest.TestCase):
    def test_title_name_mapping_and_all_explicit_filters(self):
        f={'books':[{'id':1,'name':'程序基础','author':'甲','publisher':'甲'}, {'id':2,'name':'程序基础练习','author':'乙','publisher':'甲'}, {'id':3,'name':'程序基础','author':'甲','publisher':'乙'}]}
        self.assertEqual([1,2,3],requested_book_ids(f,{'title':'程序基础'}))
        self.assertEqual([1],requested_book_ids(f,{'title':'程序基础','author':'甲','publisher':'甲'}))
        self.assertEqual([],requested_book_ids(f,{'title':'程序基础','author':'乙','publisher':'乙'}))

if __name__=='__main__':unittest.main()
