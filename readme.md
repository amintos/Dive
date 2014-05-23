Pattern matching on composite objects
=====================================

What's inside
-------------

The ***dive*** package provides a pattern matching facility which works directly with Python objects (think *regular expressions on object graphs*). It provides a set of basic patterns, such as matching an attribute or an object's type but also provides mechanisms of capturing matched parts of the object graph (think *variables in Prolog*). 

As matching is non-deterministic, the API uses callbacks to signal all possible matches (and instantiations of the used *Variables*) and failure. The architecture decouples a pattern's definition, its application and the interpretation of its results.

How to use
----------

*Under construction.*
See the module comment in ```dive/patterns.py```