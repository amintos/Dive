class Unifiable(object):
    """Base class for continuation-passing matchers"""

    def unify(self, value, cont, fail):
        raise NotImplemented

    def __or__(self, other):
        return Or(self, other)

    def __and__(self, other):
        return And(self, other)


class Anything(Unifiable):
    """Consumes a value and succeeds"""

    def unify(self, value, cont, fail):
        cont()

    def __repr__(self):
        return "<Anything>"
Return = Anything()


class Nothing(Unifiable):
    """Consumes a value and fails"""

    def unify(self, value, cont, fail):
        fail(self, value)

    def __repr__(self):
        return "<Nothing>"
Fail = Nothing()


class Variable(Unifiable):
    """Binds to the value matched. Only matches the bound value again."""

    _max_id = 0

    def __init__(self):
        self.id = Variable._max_id
        Variable._max_id += 1
        self.bound = False
        self.value = None

    def bind(self, value):
        self.bound = True
        self.value = value

    def unbind(self):
        self.bound = False
        self.value = None

    def unify(self, value, cont, fail):
        if self.bound:
            if value == self.value:
                cont()
            else:
                fail(self, value)
        else:
            self.bind(value)    
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

    def unify(self, value, cont, fail):
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

    def unify(self, value, cont, fail):
        try:
            self.into.unify(self.match(value), cont, fail)
        except (IndexError, KeyError, AttributeError):
            fail(self, value)


class Ensure(Match):
    """Evaluate an expression and continue if true"""

    def unify(self, value, cont, fail):
        if self.match(value):
            cont()
        else:
            fail(self, value)


class And(Unifiable):
    """Matches first argument. On success, matches second argument"""

    def __init__(self, first, second):
        self.first = first
        self.second = second

    def unify(self, value, cont, fail):
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

    def unify(self, value, cont, fail):
        self.first.unify(value,
                         cont,
                         lambda *t: self.second.unify(value, cont, fail))

    def __repr__(self):
        return "<%s or %s>" % (self.first, self.second)

#
#   Monadic patterns.
#
#   These can be chained right-associatively using the ** operator.
#   A ** B causes A to match an expression and pass the result to B.
#
#   "Return" is used as in Haskell. It matches anything and continues.
#


class PatternMonad(Unifiable):
    """Base class for chainable patterns"""

    def __pow__(self, other):
        return self.bind(other)

    def unify(self, value, cont, fail):
        self.bind(Return).unify(value, cont, fail)


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

