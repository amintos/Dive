"""
Composable units describing patterns.

Patterns can be matched using the unify() method.
Unify takes 3 Arguments:
    the_object              Some structured object being matched
    success_continuation    The method which is called for each match
    failure_continuation    Method called when the pattern does not match

    failure_continuation needs two arguments: The first being the sub-pattern
    that caused the failure and the second being the value that did not
    match that sub-pattern.

Patterns can be combined using one of the following operations:

    a & b   matches a and b. b is not evaluated if a fails.
    a | b   matches a or b. b is not evaluated if a succeeds.
    a ** b  matches a, passes the matched result to b.

    WARNING:
    Note that composition using ** associates to the RIGHT.
    a ** b ** c resolves to a ** (b ** c).
    Writing (a ** b) ** c may not work.

Available patterns are:

    Attribute('name'):
        Matches an attribute. Passes its value to the next pattern with **.
        Fails if the attribute does not exist.

    Subtype(class_or_type):
        Matches the type of an object. Passes the object to the next pattern.

    Constant(value):
        Matches exactly the given value using ==. Not composable via **.

    Variable():
        First, matches any value and stores the matched object.
        If it is matched again, it matches against the stored object.
        Passes the value via **.

        Example:
            var = Variable()
            pattern = Attribute('foo') ** var
            def cont():
                print var.value
            def fail():
                print "Nothing matched"
            pattern.unify(some_object, cont, fail)

            This will print the value of some_object.foo or print
            "Nothing matched" if some_object has no attribute "foo".

        Other Example:

            pattern = Attribute('foo') ** var & Attribute('bar') ** var

            This pattern matches only objects with attributes foo and bar
            being equal (As they get bound to the same variable).

    First:
        Matches elements of a collection. Proceeds with the first match along **.

        Example:
            var = Variable()
            pattern = First ** If(lambda x: x < 3) ** var

        Will match the first element in a collection which is less than 3
        an store it in var. In contrast to Some, First will not find further matches.

    Some:
        Matches elements of a collection. Proceeds with every match.
        Fails if nothing matched.


    Each:
        Matches elements of a collection. Proceeds with every match but
        does not fail if nothing matched. This may call neither
        a success nor a failure continuation.

    All:
        Matches all elements of a collection. Fails if any single element fails.
        Passes the elements to the next (**) pattern.

    Get(lambda x: ... ):
        Retrieve the value computed by the given function and pass it on.
        Fails on AttributeError, IndexError and KeyError

        Example: Attribute('foo') is just syntactic sugar for Get(lambda x: x.foo).

    If(lambda x: ...):
        Checks the predicate on the given object. Proceeds with this value
        if the predicate evaluates to True. Fails otherwise.

        Example:
            var = Variable()
            pattern = Each ** If(lambda x: x < 3) ** var
            patter.unify([1, 2, 3, 4], cont, fail)

            will call cont twice with var.value being 1 and 2.


"""



def fail_silent(*_):
    pass


class Unifiable(object):
    """Base class for continuation-passing matchers"""

    def unify(self, value, cont, fail=fail_silent):
        raise NotImplemented

    def bind(self, other):
        raise NotImplemented(
            "%s cannot be composed via ** as it does not yield new data." +
            "Use & or | for composition.")

    def __or__(self, other):
        return Or(self, other)

    def __and__(self, other):
        return And(self, other)


class PatternMonad(Unifiable):
    """Base class for chainable patterns"""

    def __pow__(self, other):
        return self.bind(other)

    def unify(self, value, cont, fail=fail_silent):
        self.bind(Return).unify(value, cont, fail)


class Anything(Unifiable):
    """Consumes a value and succeeds"""

    def unify(self, value, cont, fail=fail_silent):
        cont()

    def __repr__(self):
        return "<Anything>"
Return = Anything()


class Nothing(Unifiable):
    """Consumes a value and fails"""

    def unify(self, value, cont, fail=fail_silent):
        fail(self, value)

    def __repr__(self):
        return "<Nothing>"
Fail = Nothing()


class Variable(PatternMonad):
    """Binds to the value matched. Only matches the bound value again. Passes matching results to next pattern."""

    _max_id = 0

    def __init__(self):
        self.id = Variable._max_id
        Variable._max_id += 1
        self.bound = False
        self.value = None

    def bind(self, bind):
        return And(self, bind)

    def bind_to(self, value):
        self.bound = True
        self.value = value

    def unbind(self):
        self.bound = False
        self.value = None

    def unify(self, value, cont, fail=fail_silent):
        if self.bound:
            if value == self.value:
                cont()
            else:
                fail(self, value)
        else:
            self.bind_to(value)
            cont()
            self.unbind()       # backtrack after continuation returned

    def __repr__(self):
        if self.bound:
            return "<Bound Variable #%s = %s>" % (self.id, self.value)
        else:
            return "<Unbound Variable %s>" % self.id


class Constant(Unifiable):
    """Only matches a specific value"""

    def __init__(self, value):
        self.value = value

    def unify(self, value, cont, fail=fail_silent):
        if value == self.value:
            cont()
        else:
            fail(self, value)

    def __repr__(self):
        return "<Constant %s>" % self.value


class Match(Unifiable):
    """Evaluates an expression and continues to match its value"""

    def __init__(self, match, into):
        self.into = into
        self.match = match

    def unify(self, value, cont, fail=fail_silent):
        try:
            self.into.unify(self.match(value), cont, fail)
        except (IndexError, KeyError, AttributeError):
            fail(self, value)


class Ensure(Match):
    """Evaluate an expression and continue if true"""

    def unify(self, value, cont, fail=fail_silent):
        if self.match(value):
            cont()
        else:
            fail(self, value)


class And(Unifiable):
    """Matches first argument. On success, matches second argument"""

    def __init__(self, first, second):
        self.first = first
        self.second = second

    def unify(self, value, cont, fail=fail_silent):
        self.first.unify(value,
                         lambda: self.second.unify(value, cont, fail),
                         fail)

    def __repr__(self):
        return "<%s and %s>" % (self.first, self.second)


class Or(Unifiable):
    """Matches first argument. On failure, matches second argument"""

    def __init__(self, first, second):
        self.first = first
        self.second = second

    def unify(self, value, cont, fail=fail_silent):
        self.first.unify(value,
                         cont,
                         lambda *t: self.second.unify(value, cont, fail))

    def __repr__(self):
        return "<%s or %s>" % (self.first, self.second)


class MatchAny(Unifiable):
    """Match elements of a collection."""

    def __init__(self, must_exist, only_once, into):
        self.into = into
        self.must_exist = must_exist
        self.only_once = only_once

    def unify(self, value, cont, fail=fail_silent):
        matched_once = []

        def continuation():
            matched_once[:] = [True]
            cont()

        for entry in value:
            self.into.unify(entry, continuation, fail_silent)
            if self.only_once and matched_once:
                break

        if self.must_exist:
            if not matched_once:
                fail(self, value)


class MatchAll(Unifiable):
    """Match all elements of a collection. Fail if a single one fails"""

    def __init__(self, into):
        self.into = into

    def unify(self, value, cont, fail=fail_silent):
        failed_once = False

        def failure(*_):
            global failed_once
            failed_once = True

        for entry in value:
            self.each.unify(entry, cont, failure)
            if failed_once:
                fail(self, value)
                break
#
#   Monadic patterns.
#
#   These can be chained right-associatively using the ** operator.
#   A ** B causes A to match an expression and pass the result to B.
#
#   "Return" is used as in Haskell. It matches anything and continues.
#


class Attribute(PatternMonad):
    """Chainable pattern looking up an attribute."""

    def __init__(self, name):
        self.name = name

    def bind(self, bind):
        return Match(lambda value: getattr(value, self.name), bind)


class Subtype(PatternMonad):
    """Chainable pattern asserting a certain type"""

    def __init__(self, subtype):
        self.subtype = subtype

    def bind(self, bind):
        return Ensure(lambda value: isinstance(value, self.subtype), bind)


class Index(PatternMonad):
    """Chainable pattern causing an index lookup"""

    def __init__(self, index):
        self.index = index

    def bind(self, bind):
        return Match(lambda value: value[self.index], bind)


class Get(PatternMonad):
    """Extract a value using the given function"""

    def __init__(self, extractor):
        self.extractor = extractor

    def bind(self, bind):
        return Match(self.extractor, bind)


class If(PatternMonad):
    """Continue to match if condition is satisfied"""

    def __init__(self, condition):
        self.condition = condition

    def bind(self, bind):
        return Ensure(self.condition, bind)


class Any(PatternMonad):
    """Match elements inside collection, skipping those which do not match.
    must_exist: fail if no element matched.
    only_once: cut iteration after first match"""

    def __init__(self, must_exist=1, only_once=1):
        self.must_exist = must_exist
        self.only_once = only_once

    def bind(self, bind):
        return MatchAny(self.must_exist, self.only_once, bind)

Some = Any(True, False)     # Match at least one element (or more)
First = Any(True, True)     # Match the first element
Each = Any(False, False)    # Match just each element (including none)


class All(PatternMonad):
    """Matches all elements inside collection. Fails if any does not match"""

    def bind(self, bind):
        return MatchAll(bind)
