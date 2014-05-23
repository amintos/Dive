Simple pattern matching on object structures
============================================

The *dive* library allows to match finite structures inside object graphs.

```
from dive import *

# This is our object graph:

class Simple(object):
 
    def __init__(self, foo):
        self.foo = foo

class Sophisticated(object):

    def __init__(self, foo, bar):
        self.foo = foo
        self.bar = bar
 
object_under_test = Sophisticated(23, Simple(42))
 
# We want to extract some variable

var = Variable()

def matched():
    # Will be called for each match
    print var.value

pattern1 = (Subtype(Sophisticated) ** Attribute('bar') ** Attribute('foo') ** var) 
pattern2 = pattern1 | Attribute('foo') ** var

pattern2.unify(object_under_test, matched)

```

