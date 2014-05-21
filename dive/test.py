from patterns import *
import unittest

class TestUnifiable(unittest.TestCase):

    def setUp(self):
        self.failed = False
        self.unified = False

    def should_fail(self, term1, term2):
        self.failed = True

    def should_not_fail(self, term1, term2):
        self.fail("Should not fail on %s and %s" % (term1, term2))

    def should_not_unify(self):
        self.fail("Should not have matched")

    def assert_unifies(self, pattern, against, continuation=lambda:None):
        def inner_continuation():
            self.unified = True
            continuation()
            
        pattern.unify(against, inner_continuation, self.should_not_fail)
        self.assertTrue(self.unified)

    def assert_fails(self, pattern, against):
        pattern.unify(against, self.should_not_unify, self.should_fail)
        self.assertTrue(self.failed)


class Mock(object):

    def __init__(self, foo):
        self.foo = foo


class MockMock(object):

    def __init__(self):
        self.foo = 42
        self.bar = [1, 2, 3]
        self.mock = Mock(42)

        
class TestPatterns(TestUnifiable):

    def test_anything(self):
        self.assert_unifies(Anything(), 42)
        self.assert_unifies(Anything(), '42')

    def test_nothing(self):
        self.assert_fails(Nothing(), 42)
        self.assert_fails(Nothing(), '42')

    def test_variable_binds(self):
        v = Variable()
        
        def continuation():
            self.assertEqual(v.value, 42)
            
        self.assert_unifies(v, 42, continuation)

    def test_variable_unifies_on_binding(self):
        v = Variable()
        
        def continuation():
            self.assert_unifies(v, 42)
            self.assert_fails(v, 21)
            
        self.assert_unifies(v, 42, continuation)

    def test_attribute(self):
        m = Mock(42)
        self.assert_unifies(Attribute('foo'), m)

    def test_attribute_missing(self):
        m = Mock(42)
        self.assert_fails(Attribute('bar'), m)

    def test_subtype(self):
        m = Mock(42)
        self.assert_unifies(Subtype(Mock), m)

    def test_wrong_subtype(self):
        self.assert_fails(Subtype(Mock), 42)

    def test_and(self):
        v = Variable()
        
        def continuation():
            self.assertEqual(42, v.value)
            
        self.assert_unifies(And(Anything(), v), 42, continuation)
        self.assert_unifies(And(v, Anything()), 42, continuation)

    def test_not_and(self):
        self.assert_fails(And(Anything(), Nothing()), 42)
        self.assert_fails(And(Nothing(), Anything()), 42)
        self.assert_fails(And(Nothing(), Nothing()), 42)

    def test_or(self):
        v = Variable()

        def continuation1():
            self.assertEqual(42, v.value)

        def continuation2():
            # v should not be bound
            self.assertEqual(None, v.value)

        self.assert_unifies(Or(v, Nothing()), 42, continuation1)
        self.assert_unifies(Or(Nothing(), v), 42, continuation1)
        self.assert_unifies(Or(Anything(), v), 42, continuation2)

    def test_not_or(self):
        self.assert_fails(Or(Nothing(), Nothing()), 42)

    def test_index(self):
        list = [1, 2, 3]
        v = Variable()

        def continuation():
            self.assertEqual(2, v.value)
            self.assert_fails(Index(0) ** v, list)

        self.assert_unifies(Index(1) ** v, list, continuation)

    def test_pattern(self):
        m = MockMock()
        v1 = Variable()
        v2 = Variable()

        def continuation1():
            self.assertEqual(2, v1.value)

        def continuation2():
            self.assertEqual(42, v2.value)

        pattern1 = Attribute('bar') ** Index(1) ** v1
        self.assert_unifies(pattern1, m, continuation1)

        pattern2 = (pattern1
                    & Attribute('foo') ** v2
                    & Attribute('mock') ** Attribute('foo') ** v2)
        self.assert_unifies(pattern2, m, continuation2)



        
if __name__ == '__main__':
    unittest.main()
