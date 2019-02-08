"""
Example unit tests for dummy package
"""
import unittest
import desc.dummy

class dummyTestCase(unittest.TestCase):
    def setUp(self):
        self.message = 'Hello, world'

    def tearDown(self):
        pass

    def test_run(self):
        foo = desc.dummy.dummy(self.message)
        self.assertEqual(foo.run(), self.message)

    def test_failure(self):
        self.assertRaises(TypeError, desc.dummy.dummy)
        foo = desc.dummy.dummy(self.message)
        self.assertRaises(RuntimeError, foo.run, True)

if __name__ == '__main__':
    unittest.main()
