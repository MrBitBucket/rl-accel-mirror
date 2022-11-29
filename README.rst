PyRXP is a Python language wrapper around the excellent RXP parser, a validating, namespace-aware
XML parser written in C.

*A quick example:*
::
    >>> import pyRXPU
    >>> rxp=pyRXPU.Parser()
    >>> rxp('<a>some text</a>')
    ((u'a', None, [u'some text'], None)))


RXP is based on the W3C XML 1.0 recommendation of 10th February 1998
and the Namespaces recommendation of 14th January 1999.  Deviations
from these recommendations should probably be considered as bugs.
