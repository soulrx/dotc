# dotc
DOTC (like Yahtzee) - Access Nested Dicts and Lists via Dots (Dotc objects all the way down) 

pip install dotc
python
from dotc import Dotc

Converts Python Data Structures (dicts, lists, scalars) to a nested object structure

    - can access nested data with dot notation and _listindex for lists

      - example:
            data = {'a':1,'b':{'c':3,'d':[4,5,'6']}}
            node = 'root' # optional node name; defaults to '', but child nodes get their names from keys
            o = Dotc(data,node) or o = Dotc(data=data,node='root')
            o.a returns 1
            o.b.c returns 3
            o.b.d._0 returns 4
    
    - if _strict=0 (default), accessing a non-existent attribute returns _default instead of raising AttributeError

      - example using o from above:
            o.b.x returns None (the default _default value)

    - if _strict=1, setting a value on a non-existent path raises an exception

    - if setting _strict=1 after instantiation, it has no effect on child nodes (TODO: fix with @property(s))

    - use ._ to get fully resolved data structure otherwise ._val is the scalar/resultant value if set
        otherwise the Dotc object is returned so you can keep traversing with dot notation

      - example using d from above:
            o._ returns {'a':1,'b':{'c':3,'d':[4,5,'6']}}
            o.b._ returns {'c':3,'d':[4,5,'6']} where as d.b returns the Dotc object itself so that:
            o.b.d._ returns [4,5,'6']

    - explore (using o from above) passing in the dotc object (or not for self) 
        and optionally v for verbosity:
        
        >>> o._show()
        {'_key_ct': 2,
        '_ls_ct': 0,
        '_node': 'root',
        '_parent': None,
        '_strict': 0,
        '_val': None}

        >>> o._show(v=1)
        {'_key_ct': 2,
        '_ls_ct': 0,
        '_node': 'root',
        '_parent': None,
        '_strict': 0,
        '_val': None,
        'a': 1,
        'b': Dotc( "b", _val=None, _key_ct=2, _ls_ct=0 )}

        >>> o._show(o.b.d, v=1)
        {'_0': 4,
        '_1': 5,
        '_2': '6',
        '_key_ct': 0,
        '_ls_ct': 3,
        '_node': 'd',
        '_parent': 'b',
        '_strict': 0,
        '_val': None}