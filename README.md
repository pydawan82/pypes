Pypes
====

A Java-like stream pipeline library. Allows creating nicer functional code.

Example
====
```python
stream = Stream(range(10))
(stream
 .map(lambda x: x**2)
 .filter(lambda x: x%2==0)
 .for_each(print)
 )
```

Computation efficiency:
====
This is python, who cares.