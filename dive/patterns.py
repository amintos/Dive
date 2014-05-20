class UnificationFailed(Exception):

    def __init__(self, term1, term2):
        Exception.__init__(self)
        self.term1 = term1
        self.term2 = term2

    def __repr__(self):
        return "Cannot unify %s with %s" % (self.term1, self.term2)
    __str__ = __repr__


def epic_fail(term1, term2):
    raise UnificationFailed(term1, term2)


class Unifiable(object):

    def unify(self, value, cont, fail):
        raise NotImplemented


class Anything(Unifiable):

    def unify(self, value, cont, fail):
        cont()

    def __repr__(self):
        return "<Anything>"


class Nothing(Unifiable):

    def unify(self, value, cont, fail):
        fail(self, value)

    def __repr__(self):
        return "<Nothing>"


class Variable(Unifiable):

    _max_id = 0

    def __init__(self):
        self.id = Variable._max_id
        Variable._max_id += 1
        self.unbind()

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
            self.unbind()

    def __repr__(self):
        if self.bound:
            return "<Bound Variable #%s = %s>" % (self.id, self.value)
        else:
            return "<Unbound Variable %s>" % (self.id)


class Constant(Unifiable):

    def __init__(self, value):
        self.value = value

    def unify(self, value, cont, fail):
        if value == self.value:
            cont()
        else:
            fail(self, value)

    def __repr__(self):
        return "<Constant %s>" % self.value


class Attribute(Unifiable):

    def __init__(self, name, match):
        self.name = name
        self.match = match

    def unify(self, value, cont, fail):
        try:
            self.match.unify(getattr(value, self.name), cont, fail)
        except AttributeError:
            fail(self, value)

    def __repr__(self):
        return "<Attribute %s>" % self.name

            
class Subtype(Unifiable):

    def __init__(self, subtype):
        self.subtype = subtype

    def unify(self, value, cont, fail):
        if isinstance(value, self.subtype):
            cont()
        else:
            fail(self, value)

    def __repr__(self):
        return "<Type %s>" % self.subtype.__name__


class And(Unifiable):

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

    def __init__(self, first, second):
        self.first = first
        self.second = second

    def unify(self, value, cont, fail):
        self.first.unify(value,
                         cont,
                         lambda *t: self.second.unify(value, cont, fail))

    def __repr__(self):
        return "<%s or %s>" % (self.first, self.second)


