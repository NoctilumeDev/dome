import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import primary_match, goal_rows_match, facts_match

class MeasurementTest(unittest.TestCase):
    def test_no_silent_publisher_drop_or_keyword_substitution(self):
        rule={'kind':'fields','intents':['SEARCH_BOOK'],'required':{'title':'程序基础','publisher':'出版社甲'},'requireNoOtherFilters':True}
        p={'action':'QUERY','intent':'SEARCH_BOOK','title':'程序基础','publisher':None,'keywords':['出版社甲'],'timeOption':'ALL'}
        self.assertFalse(primary_match(p,rule,'library'))
        p.update(publisher='出版社甲',keywords=[])
        self.assertTrue(primary_match(p,rule,'library'))
    def test_no_vacuous_educational_fit_from_keyword_or_facts(self):
        self.assertFalse(goal_rows_match([{'name':'高等数学','description':'教材','category':'数学'}],{'target':'arithmetic'}))
        self.assertFalse(goal_rows_match([{'name':'算术练习','description':'练习册'}],{'target':'arithmetic','material':'textbook'}))
        self.assertTrue(goal_rows_match([{'name':'算术入门','description':'教材'}],{'target':'arithmetic','material':'textbook'}))
    def test_empty_rows_do_not_prove_all_history_negative(self):
        self.assertFalse(primary_match({'action':'QUERY','intent':'SEARCH_BOOK'}, {'kind':'unsupported','temporalAxis':'past'},'library'))
        self.assertTrue(primary_match({'action':'CLARIFY'}, {'kind':'unsupported','temporalAxis':'past'},'library'))

if __name__=='__main__':unittest.main()
