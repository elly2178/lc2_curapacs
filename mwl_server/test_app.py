import unittest
from app import Worklist
  
class TestWorklists(unittest.TestCase):
    def test_hashme(self):
        obj = Worklist()
        self.assertEqual(obj.hashme("2020-03-18_12-17.wl"),"6c71f5c7d59100c636164ccdbcb6d453a68657c3")


