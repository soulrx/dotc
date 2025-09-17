
# DataPath imports and support functions
###################################################################################################
from copy import copy
import sys, traceback
from pprint import PrettyPrinter

pp = PrettyPrinter().pprint

def bug(msg, debug=False):
    if debug:
        print(f"DEBUG: {msg}")


# string to obj
###################################################################################################
def isnum(n):
    try: return 1 if float(n) != '' else 0
    except: return 0

def isint(n):
    try: return 1 if isnum(n) and not '.' in str(n) else 0
    except: return 0

def xnum(n):
    try: n = float(n) if '.' in n else int(n)
    finally: return n

def isbool(o):
    if o in ( True, False ):
        return True
    if isinstance(o,str) and o.lower() in ( 'true', 'false' ):
        return True
    return False

def xbool(o):
    if o in ( True, False ):
        return o
    if isinstance(o,str) and o.lower() in ('true','1'):
        return True
    if isinstance(o,str) and o.lower() in ('false','0'):
        return False
    return o

def str2obj(s):
    s = xbool(s)
    s = xnum(s)
    return s


class DataPath:
    ''' Don't have time to replace and test PathGet so this is similar but includes a setter and only static functions at this point '''

    def __init__(self) -> None:
        ...

    """ Traverses dotpath returning object or default
        example:
            n = {'t1':{'a':{},'b':[1,3,52,4]}}
            getObj('t1.b.2',n) returns 52, getObj('t1.c',n,[]) returns [], getObj('t1.b',n,[]) returns [1,3,52,4]
    """
    @staticmethod
    def get(path, obj=None, default=False, sepr=None, onebased=0, esc=None, placeholder=None, debug=0):
        try:
            SEPARATOR = sepr or '.'
            esc = esc or '\\'
            placeholder = placeholder or '~~~'
            path = path.replace(esc+SEPARATOR,placeholder)
            for p in path.split(SEPARATOR):
                p = p.replace(placeholder,SEPARATOR)

                if isinstance(obj,Dotc):
                    if obj._is_list_index(p):
                        index = int(p) if isint(p) else int(p[1:])-1 if onebased else int(p[1:])
                        if index < 0:
                            return default
                        this_kindex = f'_{index}' if not obj._onebased else f'_{index+1}'
                        obj = getattr(obj, this_kindex, default)
                    else:
                        obj = obj._get(p, default=default, onebased=onebased, esc=esc, sub=placeholder, debug=debug)

                elif isnum(p) and isinstance(obj,(list,tuple)):
                    index = int(p)-1 if onebased else int(p)
                    if index < 0:
                        return default
                    obj = obj[index]
                elif isnum(p):
                    obj = obj.get(p) or obj.get(int(p)) or obj.get(float(p))
                elif hasattr(obj,p):
                    obj = getattr(obj,p)
                else:
                    obj = obj[p]

            if isinstance(obj,Dotc):
                bug(f'final obj: got Dotc object {obj=}', debug)
                if hasattr(obj,'_val') and hasattr(obj, '_default') and obj._val != obj._default:
                    obj = obj._val
                elif hasattr(obj,'_val') and hasattr(obj, '_default'):
                    try: obj = obj._
                    except: obj = default
                else:
                    obj = default

            return obj

        except:
            return default


    ''' Traverses dotpath setting value and returning success boolean
    - must be consistent with int_as_list - either integers intrepreted as lists or dicts
    - needs more examples testing and documentation
    '''
    @staticmethod
    def set(path, val=None, obj=None, default=None, int_as_list=False, sepr=None, onebased=0, esc=None, placeholder=None, debug=False):
        o = obj
        default = {} if default is None else default
        SEPARATOR = sepr or '.'
        esc = esc or '\\'
        placeholder = placeholder or '~~~'
        dpaths = []

        # Inner Functions

        def setobj(o,k,v):
            # sets the given data object node, o, with key (k), value (v)
            nonlocal dpaths
            if isinstance(o,dict):
                o[k] = v
            elif isinstance(o,list):
                o.append(v)
            elif isinstance(o,tuple):
                o = list(o)
                index = int(k)-1 if onebased else int(k)
                if len(o) > index:
                    o[index] = v
                else:
                    o.append(v)
                o = tuple(o)
            elif hasattr(o,'__dict__'):
                setattr(o,k,v)
            else:
                raise Exception(f'unknown container @ {".".join(dpaths)}')

        def new_empty_container(p):
            # since we are creating a new container, we must be consistent with int_as_list=0/1
            if isint(p) and int_as_list:
                return []
            elif isint(p):
                return {}
            else:
                return default

        def missing_container(p,o):
            # only applies to paths up to the last one - the last one is for setting the value
            gotten_container = DataPath.get( p.replace(SEPARATOR,esc+SEPARATOR), o, onebased=onebased, esc=esc )
            return 0 if isinstance(gotten_container,(dict,list,tuple)) or hasattr(gotten_container,'__dict__') else 1

        try:
            paths = path.replace(esc+SEPARATOR,placeholder).split(SEPARATOR)
            paths = [ p.replace(placeholder,SEPARATOR) for p in paths ]
            for i,p in enumerate(paths):
                if SEPARATOR in p:
                    dpaths.append(p.replace(SEPARATOR,esc+SEPARATOR))
                else:
                    dpaths.append(p)

                still_traversing_paths = 0 if i == len(paths)-1 else 1
                if still_traversing_paths: # to get to next object node, o
                    next_path = paths[ i+1 ]
                    if missing_container(p,o):
                        next_container = new_empty_container( next_path )
                        setobj( o, p, copy(next_container) )

                        if isinstance(o,dict):
                            o = o[p]
                        elif isinstance(o,(list,tuple)):
                            o = o[-1]
                        elif hasattr(o,'__dict__'):
                            o = getattr(o,p)

                    else:
                        o = DataPath.get( p.replace(SEPARATOR,esc+SEPARATOR), o, onebased=onebased, esc=esc )

                    if debug: print(f'{".".join(dpaths)} , next o = {o=}')

                else: # lasrun
                    if debug: print('.'.join(dpaths))
                    setobj(o,p,val)

        except Exception as e:
            if debug:
                print(traceback.format_exc())
                print(sys.exc_info()[2])
            return False

        else:
            return True

        # Dynamic Sublclassing seems interesting; https://stackoverflow.com/questions/9269902/is-there-a-way-to-create-subclasses-on-the-fly
        # SubClass = type('SubClass', (EntityResource,), {}) or just instantated = type('name',(),{})

    @staticmethod
    def rm(path, obj=None, default=False, sepr=None, onebased=0, esc=None, placeholder=None, debug=0):
        try:
            SEPARATOR = sepr or '.'
            esc = esc or '\\'
            placeholder = placeholder or '~~~'
            path = path.replace(esc+SEPARATOR,placeholder)

            evicted = DataPath.get(path, obj, default, sepr, onebased, esc, placeholder, debug)
            if evicted == False:
                return True

            stems = path.split(SEPARATOR)
            stems = [ s.replace(placeholder,SEPARATOR) for s in stems ]
            stem = stems.pop()

            if not stems:
                parent = obj
            else:
                parent = DataPath.get(f'{SEPARATOR}'.join(stems), obj)

            if isinstance(parent,dict):
                del parent[stem]

            # need to fix up tuple and list handling
            elif isinstance(parent,(list,tuple)) and isint(stem):
                index = int(stem)-1 if onebased else int(stem)
                if not 0 <= index <= (len(parent)-1):
                    return True
                _ = parent.pop(index)
                return True

            elif isinstance(parent,(list,tuple)) and not isint(stem):
                raise Exception('non-integer key in list or tuple')

        except Exception as e:
            if debug:
                print(traceback.format_exc())
                print(sys.exc_info()[2])
            return default


from numbers import Number
from typing import Any

def is_scalar(obj: Any) -> bool:
    """
    Checks if an object is a scalar. This includes numbers, booleans, strings,
    bytes, and None.
    """
    # Use the abstract base class for a robust number check
    if isinstance(obj, Number):
        return True

    # Check for other common scalar types
    if isinstance(obj, (str, bytes, type(None))):
        return True

    # Dictionaries, lists, sets, and other mutable containers are not scalars
    return False

from collections.abc import Iterable
def is_iterable(obj: Any) -> bool:
    """
    Checks if an object is iterable (like a list, tuple, or set) but not a string or bytes.
    """
    if isinstance(obj, (str, bytes)):
        return False
    return isinstance(obj, Iterable)

""" self.__version__ = '0.3.1'

NOTE 0.3.1
- A decent working state excepting escaping and subsitutions, which have not been tested
- can set _default during instantiation only; default: _default=None
  - accessing a non-existent attribute returns _default instead of raising AttributeError
  - setting ._strict=1 raises AttributeError if attribute not found
  - setting ._strict=1 after instantiation has no effect on child nodes (can fix with @property def _strict)
- access nested data structs with dot notation and _listindex for lists
- use ._ to get fully resolved data structure otherwise ._val is the scalar value if set
  and its Dotc objects all the way down
- shared attrs is no longer a problem
- got rid of all of the printed AttributeErrors except when _debug > 1

TODO:
- sort bug printing by levels
- fix _strict not being propagated to child nodes
- convert all applicable methods to @property(s)
- need unit tests
- need consistent prms in all the _ methods

"""
class Dotc:
    """ Converts Python Data Structures (dicts, lists, scalars) to a nested object structure
    - can access nested data with dot notation and _listindex for lists
      - example:
            data = {'a':1,'b':{'c':3,'d':[4,5,6]}}
            node = 'root' # optional node name; defaults to '', but child nodes get their names from keys
            d = Dotc(data,node) or d = Dotc(data=data,node='root')
            d.a returns 1
            d.b.c returns 3
            d.b.d._0 returns 4
    - if _strict=0 (default), accessing a non-existent attribute returns _default instead of raising AttributeError
      - example using d from above:
            d.b.x returns None (the default _default value)
    - if _strict=1, setting a value on a non-existent path raises an exception
    - if setting _strict=1 after instantiation, it has no effect on child nodes (TODO: fix with @property(s))
    - use ._ to get fully resolved data structure otherwise ._val is the scalar/resultant value if set
        otherwise the Dotc object is returned so you can keep traversing with dot notation
      - example using d from above:
            d._ returns {'a':1,'b':{'c':3,'d':[4,5,6]}}
            d.b._ returns {'c':3,'d':[4,5,6]} where as d.b returns the Dotc object itself so that:
            d.b.d._ returns [4,5,6]
    """
    def __init__(self, data=None, node=None, default=None, **kw):
        self._debug = int(kw.pop('_debug', 0)) or int(kw.pop('debug', 0))
        self._prefix = kw.pop('_prefix', '_')
        self._sepr = kw.pop('_sepr', '.')
        self._onebased = kw.pop('_onebased', 0)
        self._parent = kw.pop('_parent', None)
        self._esc = kw.pop('_esc', '\\')
        self._sub = kw.pop('_sub', '~~~')
        self._default = default if default is not None else kw.pop('_default', None)
        self._strict = kw.pop('_strict', 0)  # if 1, then setting a value on a non-existent path raises an exception

        self._attrs = ['_version','_debug','_prefix','_sepr','_onebased','_node','_parent','_esc','_sub']
        self._attrs += ['_default','_strict']
        self._methods_primary = ['_get', '_get_val', '_get_data', '_set', '_set_val', '_set_data', '_data', '_to_pathdict']
        self._methods_other = ['_show', '_to_lsprms', '_is_scalar', '_is_list_index', '_get_data_keys', '_get_list_keys', '_get_dict_keys']
        self._methods_other += ['_is_empty_dotc', '_resolve', '_clear_data_attributes']
        self._containers_primary = ['_val']
        self._containers_other = ['_attrs', '_methods', '_special_containers', '_containers_other', '_containers_primary', '_methods_primary', '_methods_other']
        self._methods = set(self._methods_primary + self._methods_other)
        self._special_containers = set(self._containers_primary + self._containers_other)

        # self._ will be a reserved method for resolving all data within a dotc object
        self._clear_data_attributes()
        self._val = kw.pop('_val', None) # this is for scalar data or result of a data path get
        self._node = node if node is not None else kw.pop('_node', '')
        _data = kw.pop('_data', None)
        data = _data if _data is not None else data
        if data is not None:
            self._set_data(data)
        self._path = kw.pop('_path', self._node if self._node else '')
        self._pathget = kw.pop('_pathget', None)

    def __repr__(self):
        return f'Dotc( "{self._node}", _val={repr(self._val)}, _key_ct={len(self._get_dict_keys())}, _ls_ct={len(self._get_list_keys())} )'

    def __getattribute__(self, name):
        # Always use object.__getattribute__ to avoid recursion.
        # This will get the attribute from the parent class (object)
        # without calling this method again.
        if name == '_val':
            return object.__getattribute__(self, name)
        #elif name == '_': # this is handled by the @property def _()
        #    return object.__getattribute__(self, '_resolve')()

        try:
            strict = object.__getattribute__(self, '_strict')
            default = object.__getattribute__(self, '_default')
            debug = object.__getattribute__(self, '_debug')
            attr = object.__getattribute__(self, name)
        except AttributeError:
            msg = f'warning: AttributeError caught (could just be part of backfilling missing containers): {name=}, {strict=}, {default=}'
            if int(debug) > 1:
                print(msg)
            if strict:
                raise AttributeError(f'{msg}')
            else:
                return default

        # This uses the default attribute lookup.
        if hasattr(attr, '_val') and attr._val is not default:
            return attr._val

        return attr

    def __call__(self, path=None):
        if not isinstance(path, (str, bytes)) or not path:
            return self._default
        data = self._resolve()
        res = DataPath.get(path, data, self._default, self._sepr, self._onebased, self._esc, self._sub, self._debug)
        return res

    @property
    def _(self):
        if self._val is not self._default:
            return self._val
        return self._resolve()

    def _clear_data_attributes(self):
        # This is a new helper method
        data_keys = self._get_data_keys()
        for k in list(data_keys):
            delattr(self, k)
        # Clear _val as well if it was set
        self._val = self._default

    def _show(self,o=None,v=0):
        ''' cli tool to inspect dotc objects 
        o is dotc object or None for self
        v is verbosity level; 0=minimal, 1=more, 2=most
        example:
            d = Dotc(data={'a':1,'b':{'c':3,'d':[4,5,6]}})
            d._pd() and d._pd(v=1) for more detail
        '''
        o = o if o is not None else self
        if not isinstance(o,Dotc):
            pp(o)
        else:
            dict_keys = o._get_dict_keys()
            list_keys = o._get_list_keys()
            _key_ct=len(dict_keys)
            _ls_ct=len(list_keys)
            dict_print = dict(_ls_ct=_ls_ct, _key_ct=_key_ct)
            display_keys = { k for k,v in o.__dict__.items() if k not in o._attrs and k not in o._methods and k not in o._containers_other }
            if v < 1:
                for k in list(dict_keys) + list(list_keys):
                    display_keys.remove(k) if k in display_keys else None
            elif v > 1:
                display_keys = { k for k,v in o.__dict__.items() if k not in o._containers_other }
            display_keys.add('_node')
            display_keys.add('_parent')
            display_keys.add('_strict')
            dict_print.update({ k:getattr(o,k) for k in display_keys })
            pp(dict_print)

    def _is_list_index(self, obj):
        """
        Checks if an object is a special list index key (e.g., '_<index>').
        """
        if isint(obj):
            return True
        if not isinstance(obj, (str, bytes)):
            return False
        o = copy(obj)
        if isinstance(o, bytes):
            try: o = o.decode('utf-8', errors='ignore')
            except: return False
        if not o.startswith(self._prefix):
            return False
        o = o[len(self._prefix):]
        if not isint(o):
            return False
        return True

    def _is_empty_dotc(self, obj=None):
        o = obj if obj is not None else self
        if isinstance(o, Dotc) and len(o._get_data_keys()) == 0:
            if self._val is self._default or not self._val:
                return True
        return False

    def _to_pathdict(self, d=None, lspp=None, default=None, onebased=None, sepr=None, getprm=None, debug=0):
        # needs handle nested list,dict,Dotc objects so that resulting setprms can be used to reconstruct the original object
        ONEBASED = onebased if onebased is not None else self._onebased
        SEPR = sepr if sepr is not None else self._sepr
        DEFAULT = default if default is not None else self._default
        lspp = lspp if lspp is not None else []
        getprm = getprm if getprm is not None else {}
        def addprms(d, lspp, getprm):
            if isinstance(d, Dotc):
                dotcnode = d._node
                if d._val is not DEFAULT:
                    dpath = SEPR.join(lspp) if lspp else '_val'
                    getprm[dpath] = d._val
                    return
                data_keys = d._get_data_keys()
                for k in data_keys:
                    v = getattr(d,k)
                    # send a list of paths out including the new key (k)
                    lspp_out = lspp[:] + [ str(k) ]
                    addprms( v, lspp_out, getprm )
            elif hasattr(d, '__dict__') or isinstance(d, dict):
                items = d.items() if isinstance(d, dict) else d.__dict__.items()
                for k,v in items:
                    # send a list of paths out including the new key
                    lspp_out = lspp[:] + [ str(k) ]
                    addprms( v, lspp_out, getprm )
            elif is_iterable(d):
                ndx = 0 if ONEBASED else -1
                for v in list(d):
                    ndx += 1
                    # send a list of paths out including the new key (ndx)
                    lspp_out = lspp[:] + [ str(ndx) ]
                    addprms( v, lspp_out, getprm )
            # else node is done; add val or '' if no val, but store actual val object for later use
            else:
                dpath = SEPR.join(lspp)
                getprm[dpath] = d
            bug(f'_to_pathdict.addprms: {d=}, {lspp=}, {getprm=}', debug or self._debug)

        addprms(d, lspp, getprm)
        bug(f'_to_pathdict: {d=}, {lspp=}, {getprm=}', debug or self._debug)
        return getprm

    @property
    def _data_keys(self):
        return self._get_data_keys()

    def _get_data_keys(self):
        data_keys = { k for k,v in self.__dict__.items() if k and k not in self._attrs and k not in self._methods and k not in self._special_containers }
        return data_keys

    def _get_list_keys(self):
        list_keys = { k for k,v in self.__dict__.items() if self._is_list_index(k) }
        return list_keys

    def _get_dict_keys(self):
        data_keys = self._get_data_keys()
        list_keys = self._get_list_keys()
        dict_keys = data_keys - list_keys
        return dict_keys    

    def _get_data(self, path=None, obj=None, default=None, sepr=None, onebased=0, esc=None, sub=None, debug=0):
        ''' returns a fully decomposed data structure of nested dicts or lists based on getprms from pathdict '''
        o = obj if obj is not None else self
        path = path if path is not None else ''
        SEPARATOR = sepr or o._sepr
        ESC = esc or o._esc
        SUB = sub or o._sub
        ONEBASED = onebased or o._onebased
        DEFAULT = default if default is not None else o._default
        res = DEFAULT
        dotc = self if path in (None, '', b'') else self._get(path, default=DEFAULT, obj=o, sepr=SEPARATOR, onebased=ONEBASED, esc=ESC, sub=SUB, debug=debug)
        res = self._resolve(dotc, default=DEFAULT, debug=debug)
        return res

    def _get_val(self, path=None, default=None, obj=None, sepr=None, onebased=0, esc=None, sub=None, debug=0):
        ''' returns a scalar value based on path '''
        path = path if path is not None else ''
        DEFAULT = default if default is not None else self._default
        dotc = self._get(path, default=DEFAULT, obj=obj, sepr=sepr, onebased=onebased, esc=esc, sub=sub, debug=debug)
        if isinstance(dotc,Dotc):
            return dotc._val if dotc._val is not DEFAULT else DEFAULT
        return dotc

    def _get(self, path, default=None, obj=None, sepr=None, onebased=0, esc=None, sub=None, debug=0):
        try:
            o = obj if obj is not None else self
            SEPARATOR = sepr or self._sepr
            ONEBASED = onebased or self._onebased
            ESC = esc or self._esc
            SUB = sub or self._sub
            DEFAULT = default if default is not None else self._default
            path = path.replace(ESC+SEPARATOR,SUB)
            for p in path.split(SEPARATOR):
                p = p.replace(SUB,SEPARATOR)
                bug(f'getting {p} from {o=}', debug or self._debug)
                if self._is_list_index(p):
                    bug(f'list index {p=} found', debug or self._debug)
                    index = int(p) if isint(p) else int(p[len(self._prefix):])-1 if ONEBASED else int(p[len(self._prefix):])
                    bug(f'list index {p=} resolved to {index=}', debug or self._debug)
                    if index < 0:
                        bug(f'index {index} is negative', debug or self._debug)
                        return DEFAULT
                    if isinstance(o,Dotc):
                        this_kindex = f'{self._prefix}{index}' if not o._onebased else f'{self._prefix}{index+1}'
                        o = getattr(o, this_kindex, DEFAULT)
                    elif is_iterable(o) and not hasattr(o,'__dict__'):
                        try: o = list(o)[index]
                        except: o = DEFAULT
                    else:
                        return DEFAULT
                elif isinstance(o,dict):
                    try: o = o[p]
                    except: o = DEFAULT
                elif hasattr(o,p):
                    o = getattr(o,p)
                else:
                    o = DEFAULT
            return o
        except Exception as e:
            print(traceback.format_exc())
            return DEFAULT

    def _set_data(self, data, debug=0):
        # handle empty containers and scalars first
        if isinstance(data,Dotc):
            if self._is_empty_dotc(data):
                bug(f'_set_data: empty Dotc data - setting _val={data}', debug or self._debug)
                self._set_val(self, data)
                return
            bug(f'_set_data: Dotc data - will be set in _set by getprm', debug or self._debug)
        elif is_iterable(data) and ( hasattr(data,'__dict__') or isinstance(data,dict) ):
            items = data.items() if isinstance(data,dict) else data.__dict__.items()
            if len(list(items)) == 0:
                bug(f'_set_data: empty dict-like data - setting _val={data}', debug or self._debug)
                self._set_val(self, data)
                return
        elif is_iterable(data):
            if len(list(data)) == 0:
                bug(f'_set_data: empty iterable data - setting _val={data}', debug or self._debug)
                self._set_val(self, list(data))
                return
        elif is_scalar(data):
            bug(f'_set_data: scalar data - setting _val={data}', debug or self._debug)
            self._set_val(self, data)
            return
        bug(f'_set_data: complex data - setting _getprm', debug or self._debug)
         # get all the setprms from data
        getprm = self._to_pathdict(data, [], self._default, self._onebased, self._sepr)
        for k in sorted(list(getprm)):
            v = getprm[k]
            bug( f'_set_data: getprm {k=}, {v=}', debug or self._debug )
            self._set(k, v, self)

    def _set_val(self, obj, val):
        'all roads end at a Dotc object with a _val attribute'
        if isinstance(val,Dotc):
            raise Exception('_set_val: val cannot be a Dotc object')
        o = obj
        if not isinstance(o,Dotc):
            raise Exception('_set_val: obj must be a Dotc object')
        o._val = val

    def _set(self, path, val=None, obj=None, sepr=None, onebased=0, esc=None, sub=None, debug=False):
        o = obj if obj is not None else self
        bug(f'\t_set: {path=}, {val=}, {o._node=}', debug or self._debug)
        SEPARATOR = sepr or o._sepr
        ESC = esc or o._esc
        SUB = sub or o._sub
        ONEBASED = onebased or o._onebased
        NODE = '' if not hasattr(o,'_node') else o._node
        PARENT = path.rsplit(SEPARATOR,1)[0] if SEPARATOR in path else path
        dpaths = []

        def newdot( data=self._default,
                    node='',
                    _parent=NODE,
                    _sepr=SEPARATOR,
                    _esc=ESC,
                    _sub=SUB,
                    _onebased=ONEBASED,
                    _default=self._default,
                    _strict=self._strict,
                    debug=debug ):
            return Dotc(data=data,
                        _node=node,
                        _parent=_parent,
                        _sepr=_sepr,
                        _esc=_esc,
                        _sub=_sub,
                        _onebased=_onebased,
                        _default=_default,
                        _strict=_strict,
                        _debug=debug)

        if isinstance(val,Dotc) or is_iterable(val):
            v = newdot( data=val, node=path.rsplit(SEPARATOR, 1)[-1] )
        else:
            v = val
        bug(f'\t_set: prepared {v=} for setting at {path=}', debug or self._debug)


        # Inner Functions
        def missing_container(p,o):
            # only applies to paths up to the last one - the last one is for setting the value
            gotten_container = self._get( p.replace(SEPARATOR,ESC+SEPARATOR), default=SUB, obj=o )
            if gotten_container in (None, self._default):
                bug(f'~~~~~ missing container: True {p=} {o=}', debug or self._debug)
                return True
            if isinstance(gotten_container,(dict,list,Dotc)):
                bug(f'~~~~~ missing container: False {p=} {o=}', debug or self._debug)
                return False
            if gotten_container == SUB:
                bug(f'~~~~~ missing container: True {p=} {o=}', debug or self._debug)
                return True
            return False

        try:
            paths = path.replace(ESC+SEPARATOR,SUB).split(SEPARATOR)
            paths = [ p.replace(SUB,SEPARATOR) for p in paths ]
            final_path = paths[-1]
            final_index = len(paths)-1
            still_traversing = lambda i: 1 if i < final_index else 0

            # backfill if necessary
            for i,p in enumerate(paths):
                dpaths.append(p if not SEPARATOR in p else p.replace(SEPARATOR,ESC+SEPARATOR))
                curr_path = '.'.join(dpaths)
                bug(f'\n\nPATH-{i}\n\t1: {curr_path=}, {paths=} \np={p}, o={o}', debug or self._debug)

                if missing_container(p,o):
                    if self._is_list_index(p):
                        index = int(p) if isint(p) else int(p[len(o._prefix):])-1 if ONEBASED else int(p[len(o._prefix):])
                        this_kindex = f'{o._prefix}{index}' if not o._onebased else f'{o._prefix}{index+1}'
                    else:
                        this_kindex = p
                    nextdot = newdot(node=this_kindex, _parent=o._node)
                    setattr(o, this_kindex, nextdot)
                    if missing_container(p,o):
                        raise Exception(f'failed to backfill new container for {p=} @ {".".join(dpaths)}')
                    bug(f'\n\tBF1: backfilled... added {this_kindex} to {o=}', debug or self._debug)
                    o = self._get( p, default=SUB, obj=o, onebased=ONEBASED, esc=ESC )
                else:
                    o = self._get( p, default=SUB, obj=o, onebased=ONEBASED, esc=ESC )
                bug(f'GOT1: {o=} for {p=} @ {".".join(dpaths)}', debug or self._debug)


            bug(f'\n\tGOTF: last run; setting {p=} to {v=} in {o=}', debug or self._debug)

            if self._is_list_index(p):
                index = int(p) if isint(p) else int(p[len(o._prefix):])-1 if ONEBASED else int(p[len(o._prefix):])
                this_kindex = f'{o._prefix}{index}' if not o._onebased else f'{o._prefix}{index+1}'
                bug(f'\n\tGOTF1a: list index {p=} resolved to {index=}, {this_kindex=}', debug or self._debug)
                o._set_val(o, v)

            else:
                bug(f'\n\tGOTF2: setting dict key {p=} to {v=} in {o=}', debug or self._debug)
                o._set_val(o, v)


        except Exception as e:
            if debug:
                print(traceback.format_exc())
                print(sys.exc_info()[2])
            return False

        else:
            bug(f'final o: {o=}, => {v=}, {o._val=}', debug or self._debug)
            return True

        # Dynamic Sublclassing seems interesting; https://stackoverflow.com/questions/9269902/is-there-a-way-to-create-subclasses-on-the-fly
        # SubClass = type('SubClass', (EntityResource,), {}) or just instantated = type('name',(),{})

    def _resolve(self, obj=None, default=None, sepr=None, onebased=0, esc=None, sub=None, debug=False):
        """ resolves all data in a dotc object into a nested structure of dicts and lists; returns the resolved data structure or default on error """
        o = obj if obj is not None else self
        SEPARATOR = sepr or self._sepr
        ONEBASED = onebased or self._onebased
        ESC = esc or self._esc
        SUB = sub or self._sub
        PREFIX = self._prefix
        DEFAULT = default if default is not None else self._default
        dpaths = []
        res = DEFAULT

        # Inner Functions

        def setobj(o,k,v):
            # sets the given data object node, o, with key (k), value (v)
            nonlocal dpaths
            if isinstance(o,dict):
                o[k] = v
            elif isinstance(o,list):
                # backfill with None/DEFAULT if necessary
                bug(f'setting list index {k=} to {v=} in {o=}', debug or self._debug)
                index = int(k) if isint(k) else int(k[len(PREFIX):])-1 if ONEBASED else int(k[len(PREFIX):])
                while len(o) < index:
                    o.append(DEFAULT)
                o.append(v)
            elif hasattr(o,'__dict__'): # this should never happen since we are resolving to dicts and lists
                setattr(o,k,v)
            else:
                raise Exception(f'unknown container @ {".".join(dpaths)}')

        def new_empty_container(p):
            # since we are creating a new container, we must be consistent with int_as_list=0/1
            return [] if self._is_list_index(p) else {}

        def missing_container(p,o):
            # only applies to paths up to the last one - the last one is for setting the value
            gotten_container = self._get( p.replace(SEPARATOR,ESC+SEPARATOR), default=SUB, obj=o )
            if isinstance(gotten_container,(dict,list,Dotc)):
                return False
            if gotten_container == SUB:
                return True
            return False

        def set_getprm(o,paths,val):
            # sets the _getprm of the given dotc object, o, with path (k), value (v)
            if isinstance(val,Dotc):
                val = val._val # this should never happen since _to_pathdict should have decomposed all Dotc objects into paths and values
            dpaths = []
            if isinstance(val,Dotc):
                val = val._val # this should never happen since _to_pathdict should have decomposed all Dotc objects into paths and values
            bug(f'\n\nset_getprm\n\t1: {SEPARATOR.join(dpaths)}, \nval={val}, o={o}', debug or self._debug)

            for i,p in enumerate(paths):
                if SEPARATOR in p:
                    dpaths.append(p.replace(SEPARATOR,ESC+SEPARATOR))
                else:
                    dpaths.append(p)

                still_traversing_paths = 0 if i == len(paths)-1 else 1
                if still_traversing_paths: # to get to previous object node, o
                    child_node = paths[ i+1 ]
                    #child_path = SEPARATOR.join(dpaths + [child_node])
                    if missing_container(p,o):
                        next_container = new_empty_container( child_node )
                        setobj( o, p, copy(next_container) ) # backfills lists with default if necessary

                        if isinstance(o,dict):
                            o = o[p]
                        elif isinstance(o,list):
                            o = o[-1]
                        elif hasattr(o,'__dict__'): # this should never happen since we are resolving to dicts and lists
                            o = getattr(o,p)

                    else:
                        o = self._get( p.replace(SEPARATOR,ESC+SEPARATOR), default=DEFAULT, obj=o )

                    if isinstance(o,Dotc):
                        if o._val is not DEFAULT:
                            o = o._val
                        else:
                            raise Exception(f'non-scalar Dotc object found @ {".".join(dpaths)} during set_getprm')


                else: # last run
                    bug(f'\n\nset_getprm LAST RUN:\n\t {SEPARATOR.join(dpaths)}, \nval={val}, o={o}', debug or self._debug)
                    setobj(o,p,val)

        try:
            pathdict = self._to_pathdict(o, None, DEFAULT, ONEBASED, SEPARATOR, None, debug)
            if pathdict.get('_val') is not DEFAULT:
                return pathdict.get('_val')
            getprms = sorted(list(pathdict))
            bug(f'\n\nRESOLVE START: {SEPARATOR.join(dpaths)}, \npathdict={pathdict}, \ngetprms={getprms}', debug or self._debug)
            if not getprms:
                return DEFAULT
            res = [] if self._is_list_index(getprms[0].split(SEPARATOR)[0]) else {}
            for i,getprm in enumerate(getprms):
                paths = getprm.replace(ESC+SEPARATOR,SUB).split(SEPARATOR)
                paths = [ p.replace(SUB,SEPARATOR) for p in paths ]
                val = pathdict[getprm]
                set_getprm(res,paths,val)
                bug(f'\n\nRESOLVE {i}\n\t1: {SEPARATOR.join(paths)}, \nres={res}', debug or self._debug)

        except Exception as e:
            pp(res)
            if debug:
                print(traceback.format_exc())
                print(sys.exc_info()[2])
            return DEFAULT

        else:
            return res




class Pget:
    """ Traverses dotpath returning object or default """
    def __new__(cls, o1=None, o2=None, default=None, sepr=None, onebased=0, esc=None, placeholder=None, debug=0):
        # Create the instance first
        instance = super().__new__(cls)
        
        # Initialize instance attributes
        instance.default = default
        instance.sepr = sepr or '.'
        instance.onebased = onebased
        instance.esc = esc or '\\'
        instance.placeholder = placeholder or '~~~'
        instance.debug = int(debug)

        # for versatility, o1 can be data or path and o2 can be path or data
        if not isinstance(o1,(str,bytes,None.__class__)):
            instance.data = o1
            if isinstance(o2,(str,bytes)):
                instance.path = o2
        elif not isinstance(o2,(str,bytes,None.__class__)):
            instance.path = o2
            instance.data = o1
        else:
            instance.path = None
            instance.data = None
        
        # If both path and data are provided, return tuple of instance and result
        if instance.path is not None and instance.data is not None:
            result = instance.get(instance.path, instance.data, instance.default, instance.sepr, instance.onebased, instance.esc, instance.placeholder, instance.debug)
            return instance, result
        
        # Otherwise, return just the instance
        return instance
    
    def __init__(self, o1=None, o2=None, default=None, sepr=None, onebased=0, esc=None, placeholder=None, debug=0):
        # __init__ is called after __new__, but we've already done initialization in __new__
        # This can be empty or just pass
        pass

    @classmethod
    def spawn(cls, o1=None, o2=None, default=None, sepr=None, onebased=0, esc=None, placeholder=None, debug=0):
        """
        Alternative factory method that always returns a tuple of (instance, result).
        Use this if you always want both the instance and the result.
        """
        instance = cls.__new__(cls)
        instance.default = default
        instance.sepr = sepr or '.'
        instance.onebased = onebased
        instance.esc = esc or '\\'
        instance.placeholder = placeholder or '~~~'
        instance.debug = int(debug)

        # for versatility, o1 can be data or path and o2 can be path or data
        if not isinstance(o1,(str,bytes,None.__class__)):
            instance.data = o1
            if isinstance(o2,(str,bytes)):
                instance.path = o2
        elif not isinstance(o2,(str,bytes,None.__class__)):
            instance.path = o2
            instance.data = o1
        else:
            instance.path = None
            instance.data = None
        
        if instance.path is not None and instance.data is not None:
            result = instance.get(instance.path, instance.data, instance.default, instance.sepr, instance.onebased, instance.esc, instance.placeholder, instance.debug)
        else:
            result = instance.default
            
        return instance, result

    def reset(self, o1=None, o2=None, default=None, sepr=None, onebased=0, esc=None, placeholder=None, debug=0, soft=True):
        """ Resets the instance attributes and optionally sets new path and data
        - if soft is True, only updates attributes that are not None keeping previous values
        """
        if soft:
            self.default = default if default is not None else self.default
            self.sepr = sepr if sepr is not None else self.sepr
            self.onebased = onebased if onebased is not None else self.onebased
            self.esc = esc if esc is not None else self.esc
            self.placeholder = placeholder if placeholder is not None else self.placeholder
            self.debug = int(debug) if debug is not None else self.debug

            if not isinstance(o1,(str,bytes,None.__class__)):
                self.data = o1 if o1 is not None else self.data
                if isinstance(o2,(str,bytes)):
                    self.path = o2 if o2 is not None else self.path
            elif not isinstance(o2,(str,bytes,None.__class__)):
                self.path = o2 if o2 is not None else self.path
                self.data = o1 if o1 is not None else self.data
            else:
                self.path = None
                self.data = None

            if self.path is not None and self.data is not None:
                return self.get(self.path, self.data, self.default, self.sepr, self.onebased, self.esc, self.placeholder, self.debug)
            return None
        else:
            self.__init__(o1, o2, default, sepr, onebased, esc, placeholder, debug)
            if self.path is not None and self.data is not None:
                return self.get(self.path, self.data, self.default, self.sepr, self.onebased, self.esc, self.placeholder, self.debug)
            return None
        
    """ Traverses dotpath returning object or default
        example:
            from dotc import Dotc, Pget
            n = {'t1':{'a':{},'b':[1,3,52,4]}}
            pg, r = Pget('t1.b.2',n) returns obj Pget, 52
            pg.get('t1.c') returns None, pg.get('t1.b',n,[]) returns [1,3,52,4]
    """
    def get(self, path, obj=None, default=False, sepr=None, onebased=0, esc=None, placeholder=None, debug=0):
        try:
            SEPARATOR = sepr or '.'
            esc = esc or '\\'
            placeholder = placeholder or '~~~'
            path = path.replace(esc+SEPARATOR,placeholder)
            for p in path.split(SEPARATOR):
                p = p.replace(placeholder,SEPARATOR)

                if isinstance(obj,Dotc):
                    if obj._is_list_index(p):
                        index = int(p) if isint(p) else int(p[1:])-1 if onebased else int(p[1:])
                        if index < 0:
                            return default
                        this_kindex = f'_{index}' if not obj._onebased else f'_{index+1}'
                        obj = getattr(obj, this_kindex, default)
                    else:
                        obj = obj._get(p, default=default, onebased=onebased, esc=esc, sub=placeholder, debug=debug)

                elif isnum(p) and isinstance(obj,(list,tuple)):
                    index = int(p)-1 if onebased else int(p)
                    if index < 0:
                        return default
                    obj = obj[index]
                elif isnum(p):
                    obj = obj.get(p) or obj.get(int(p)) or obj.get(float(p))
                elif hasattr(obj,p):
                    obj = getattr(obj,p)
                else:
                    obj = obj[p]

            if isinstance(obj,Dotc):
                bug(f'final obj: got Dotc object {obj=}', debug)
                if hasattr(obj,'_val') and hasattr(obj, '_default') and obj._val != obj._default:
                    obj = obj._val
                elif hasattr(obj,'_val') and hasattr(obj, '_default'):
                    try: obj = obj._
                    except: obj = default
                else:
                    obj = default

            return obj

        except:
            return default
        
        finally:
            if self.data is None:
                self.data = obj

    ''' Traverses dotpath setting value and returning success boolean
    - must be consistent with int_as_list - either integers intrepreted as lists or dicts
    - needs more examples testing and documentation
    '''
    def set(self, path, val=None, obj=None, default=None, int_as_list=False, sepr=None, onebased=0, esc=None, placeholder=None, debug=False):
        o = obj
        default = {} if default is None else default
        SEPARATOR = sepr or '.'
        esc = esc or '\\'
        placeholder = placeholder or '~~~'
        dpaths = []

        # Inner Functions

        def setobj(o,k,v):
            # sets the given data object node, o, with key (k), value (v)
            nonlocal dpaths
            if isinstance(o,dict):
                o[k] = v
            elif isinstance(o,list):
                o.append(v)
            elif isinstance(o,tuple):
                o = list(o)
                index = int(k)-1 if onebased else int(k)
                if len(o) > index:
                    o[index] = v
                else:
                    o.append(v)
                o = tuple(o)
            elif hasattr(o,'__dict__'):
                setattr(o,k,v)
            else:
                raise Exception(f'unknown container @ {".".join(dpaths)}')

        def new_empty_container(p):
            # since we are creating a new container, we must be consistent with int_as_list=0/1
            if isint(p) and int_as_list:
                return []
            elif isint(p):
                return {}
            else:
                return default

        def missing_container(p,o):
            # only applies to paths up to the last one - the last one is for setting the value
            gotten_container = self.get( p.replace(SEPARATOR,esc+SEPARATOR), o, onebased=onebased, esc=esc )
            return 0 if isinstance(gotten_container,(dict,list,tuple)) or hasattr(gotten_container,'__dict__') else 1

        try:
            paths = path.replace(esc+SEPARATOR,placeholder).split(SEPARATOR)
            paths = [ p.replace(placeholder,SEPARATOR) for p in paths ]
            for i,p in enumerate(paths):
                if SEPARATOR in p:
                    dpaths.append(p.replace(SEPARATOR,esc+SEPARATOR))
                else:
                    dpaths.append(p)

                still_traversing_paths = 0 if i == len(paths)-1 else 1
                if still_traversing_paths: # to get to next object node, o
                    next_path = paths[ i+1 ]
                    if missing_container(p,o):
                        next_container = new_empty_container( next_path )
                        setobj( o, p, copy(next_container) )

                        if isinstance(o,dict):
                            o = o[p]
                        elif isinstance(o,(list,tuple)):
                            o = o[-1]
                        elif hasattr(o,'__dict__'):
                            o = getattr(o,p)

                    else:
                        o = self.get( p.replace(SEPARATOR,esc+SEPARATOR), o, onebased=onebased, esc=esc )

                    if debug: print(f'{".".join(dpaths)} , next o = {o=}')

                else: # lasrun
                    if debug: print('.'.join(dpaths))
                    setobj(o,p,val)

        except Exception as e:
            if debug:
                print(traceback.format_exc())
                print(sys.exc_info()[2])
            return False

        else:
            return True

        # Dynamic Sublclassing seems interesting; https://stackoverflow.com/questions/9269902/is-there-a-way-to-create-subclasses-on-the-fly
        # SubClass = type('SubClass', (EntityResource,), {}) or just instantated = type('name',(),{})

    def rm(self, path, obj=None, default=False, sepr=None, onebased=0, esc=None, placeholder=None, debug=0):
        try:
            SEPARATOR = sepr or '.'
            esc = esc or '\\'
            placeholder = placeholder or '~~~'
            path = path.replace(esc+SEPARATOR,placeholder)

            evicted = self.get(path, obj, default, sepr, onebased, esc, placeholder, debug)
            if evicted == False:
                return True

            stems = path.split(SEPARATOR)
            stems = [ s.replace(placeholder,SEPARATOR) for s in stems ]
            stem = stems.pop()

            if not stems:
                parent = obj
            else:
                parent = self.get(f'{SEPARATOR}'.join(stems), obj)

            if isinstance(parent,dict):
                del parent[stem]

            # need to fix up tuple and list handling
            elif isinstance(parent,(list,tuple)) and isint(stem):
                index = int(stem)-1 if onebased else int(stem)
                if not 0 <= index <= (len(parent)-1):
                    return True
                _ = parent.pop(index)
                return True

            elif isinstance(parent,(list,tuple)) and not isint(stem):
                raise Exception('non-integer key in list or tuple')

        except Exception as e:
            if debug:
                print(traceback.format_exc())
                print(sys.exc_info()[2])
            return default
