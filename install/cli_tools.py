#!/bin/env python3
# cli_tools version 1.1p
import sys
import platform
from collections import deque

# get system platform information subcommand
def _get_pfd(pf_cmd):
    d = {}
    try: d[pf_cmd] = getattr(platform,pf_cmd)()
    finally: return d

# get system platform information stored in pfd and spawn_process once
if not locals().get('pfd'):
    pf_cmds = [ 'platform', 'system', 'release', 'version' ]
    pf_cmds += [ 'python_version_tuple', 'python_implementation', 'python_compiler', 'architecture', 'machine', 'node', 'processor', 'system_alias' ]
    version_methods = [ 'mac_ver', 'freedesktop_os_release', 'win32_ver', 'java_ver', 'libc_ver' ] 
    pf_cmds += version_methods

    pfd = {}
    _ = [ pfd.update( _get_pfd(cmd) ) for cmd in pf_cmds ]

    pf_sys = pfd['system'].lower()
    pf_release = pfd['release']
    pf_version = pfd['version']
    pf_main = pfd['platform']
    pf_alias = platform.system_alias( pf_sys, pf_release, pf_version )
    pfd.update({ 'alias': pf_alias })

    # dist category and version_key
    match pf_sys:
        case 'darwin':
            dist_cat = 'macos'
            version_key = 'mac_ver'
        case 'linux':
            dist_cat = 'linux'
            version_key = 'freedesktop_os_release'
        case 'win32':
            dist_cat = 'windows'
            version_key = 'win32_ver'
        case 'java':
            dist_cat = 'java'
            version_key = 'java_ver'
        case 'unix':
            dist_cat = 'unix'
            version_key = 'libc_ver'
        case _:
            dist_cat = 'unknown'
            version_key = ''

    # dist, dct_dist, dist_version
    match dist_cat:
        case 'macos':
            dist = 'MacOS'
            dct_dist = dict( zip( ('release','versioninfo','machine'), pfd[version_key] ) )
            dist_version = dct_dist.get('release') or ''
        case 'linux':
            dct_dist = platform.freedesktop_os_release()
            dist = dict(dct_dist).get('ID')
            dist_version = dct_dist.get('VERSION_ID')
        case 'windows':
            dist = 'Windows'
            dct_dist = dict( zip( ('release','version','csd','ptype'), pfd[version_key] ) )
            dist_version = dct_dist.get('release') or ''
        case 'java':
            dist = 'Java'
            dct_dist = dict( zip( ('release','vendor','vminfo','osinfo'), pfd[version_key] ) )
            dist_version = dct_dist.get('release') or ''
        case 'unix':
            dist = 'UNIX'
            dct_dist = dict( zip( ('release','vendor','vminfo','osinfo'), pfd[version_key] ) )
            dist_version = dct_dist.get('release') or ''
        case _:
            ...


    id_sys = pf_sys[0].upper() + pf_sys[1:]
    id_distname = dist[0].upper() + dist[1:]
    id_distversion = dist_version.split(".",1)[0]
    id_dist = f'{id_distname}{id_distversion}'
    pfd.update( dict( id_sys=id_sys, id_distname=id_distname, id_distversion=id_distversion, id_dist=id_dist )  )

    #print(f'{id_dist=}')
    from subprocess import PIPE, Popen as spawn_process


class Cli:
    """ Spawns subprocess returning tuple( stdout, stderr, return code )
    - runs to completion except exceeds timeout=timeout
    - accepts:
        - cmd=cmd ; str command to be run from subshell commandline
        - timeout=timeout ; in seconds
    - stdout, stderr, & return code as self.err, self.out, self.code after each run
    """
    def __init__(self, history=100):
        self.reset()
        self.destructors = []
        self.deque = deque(maxlen=int(history))

    def __del__(self):
        for destruct in self.destructors:
            destruct(self)

    def reset(self, cmd=None):
        self.out, self.err, self.code = None, None, None
        self.cmd = cmd or ''
        self.exception = None
        if cmd and cmd.strip():
            self.deque.append(cmd)

    def history(self, last=0):
        return list(self.deque)[-1*last:]

    def trap(self, cmd, timeout=60):
        self.reset(cmd)
        # Use shell to execute the command, store the stdout and stderr in sp variable
        sp = spawn_process( cmd, shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True )
        self.code = sp.wait( timeout=timeout ) # Store return code
        self.out, self.err = sp.communicate() # separate stdout and stderr (requires the PIPE)

    def run(self, cmd, timeout=60):
        self.reset(cmd)
        try:
            self.trap( cmd, timeout )
        except Exception as e:
            self.exception = e
            print(str(e))
        finally:
            return self.out

# venv?
###################################################################################################
def is_venv(): return hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix

# passed params if main
###################################################################################################
from sys import argv
def get_args():
    args = [ a for a in argv if not '=' in a ]
    _ = args.pop(0)
    return args

def get_kw():
    kw = { k:v for k,v in ( s.split('=') for s in argv if '=' in s ) }
    return kw

def get_passed_prms():
    """ Converts cli passed params to intended types
    Returns:
        tuple of args, kw with actual ints, floats, & booleans instead of strings
    Example:
        python -i test.py test1 1 2.2 false key1=val1 key2=trUe
        from app.tools.load_tools import get_passed_prms
        args, kw = get_passed_prms()
        ==> ['test1', 1, 2.2, False], {'key1': 'val1', 'key2': True}
    """
    args = get_args()
    args = [ str2obj(s) for s in args ]
    kw = get_kw()
    kw = { k:str2obj(v) for k,v in kw.items() }
    #print(f'{args=}, {kw=}')
    return args, kw
###################################################################################################

# string to obj
###################################################################################################
def isnum(n):
    try: return 1 if float(n) != '' else 0
    except: return 0

def xnum(n):
    try: n = float(n) if '.' in n else int(n)
    finally: return n

def isbool(o):
    return True if str(o).lower() in ( 'true', 'false' ) else False

def xbool(o):
    if o in ( True, False ):
        return o
    elif isinstance(o,str) and o.lower() == 'true':
        return True
    elif isinstance(o,str) and o.lower() == 'false':
        return False
    else:
        return o

def str2obj(s):
    if not isinstance(s,str):
        return s
    if isbool(s):
        return xbool(s)
    elif isnum(s):
        return xnum(s)
    else:
        return s
###################################################################################################


# path tools

from pathlib import Path as P;

def resolve(f):
    f = str( P( f ).resolve() )
    return f

def resolve_dir(d):
    p = P( d )
    if p.is_file():
        d = resolve(d).rsplit('/',1)[0]
    elif p.is_dir():
        d = resolve(d)
    return d

def parent(o):
    p = P( o )
    if p.is_file():
        return resolve_dir( o )
    elif p.is_dir():
        return resolve_dir( f'{o.rstrip("/")}/..' )