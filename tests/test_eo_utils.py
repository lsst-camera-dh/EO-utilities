"""
Example unit tests for dummy package
"""
import unittest
#import lsst.eo_utils

class DummyTestCase(unittest.TestCase):
    """Dummy Test Class"""

    def setUp(self):
        """Called defore running tests"""
        self.message = 'Hello, world'

    def tearDown(self):
        """Called after running tests"""
        self.message = 'Done'

    def test_run(self):
        #foo = desc.dummy.dummy(self.message)
        #self.assertEqual(foo.run(), self.message)
        """Run a test"""
        self.message = "Run"

    def test_failure(self):
        #self.assertRaises(TypeError, desc.dummy.dummy)
        #foo = desc.dummy.dummy(self.message)
        #self.assertRaises(RuntimeError, foo.run, True)
        """Fail a test"""
        self.message = "Fail"

if __name__ == '__main__':
    unittest.main()
