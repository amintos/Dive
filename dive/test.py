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
        self.assert_unifies(Attribute('foo', Anything()), m)

    def test_attribute_missing(self):
        m = Mock(42)
        self.assert_fails(Attribute('bar', Anything()), m)

    def test_subtype(self):
        m = Mock(42)
        self.assert_unifies(Subtype(Mock), m)

    def test_wrong_subtype(self):
        m = Mock(42)
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
        

unittest.main()
