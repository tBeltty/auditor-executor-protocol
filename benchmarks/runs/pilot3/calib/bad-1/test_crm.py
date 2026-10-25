import unittest
from crm import CRM
class T(unittest.TestCase):
    def test_a(self):
        c=CRM([{"id":"r","role":"rep","capacity":1}]); self.assertEqual(c.add_lead("a@b.co","n","web","r"),"L1")
if __name__=="__main__": unittest.main()
