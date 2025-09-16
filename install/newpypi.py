#!/usr/bin/env python3.10
import sys
from cli_tools import Cli, pfd, id_dist, resolve, resolve_dir, parent, get_passed_prms
from pathlib import Path

# passed args,keyword-args, e.g., python -i newpypi.py name=some_proj
args, kw = get_passed_prms()

# cannot be root/admin
from os import getuid, geteuid
uid, euid = geteuid(), getuid()
if euid == 0:
    prompt = 'This is intended to be run as a normal user and not an Admin/root user.\n'
    prompt += '\nAre you sure you wish to continue? (y/n): '
    cont = input(prompt)
    if cont.lower() not in ('y','yes'):
        sys.exit()



if not( kw.get('name') or args[0] ):
  proj = input(f'\nEnter the new project name?\n')
else:
  proj = kw.get('name') or args[0]

print(f'~/Git/{proj}')
path_proj = Path(f'~/Git/{proj}')
dir_proj = resolve_dir(path_proj)

if not path_proj.is_dir():
    print(f'\n{dir_proj} was not found. Have you created and cloned the github repo yet?')
    print(f'cd ~/Git && git clone ssh://git@gh/soulrx/{proj}.git\n')

    dir_proj = input(f'\nEnter full path to new pypi project or enter to exit (so you can clone into ~/Git):\n')
    if not dir_proj:
        sys.exit()
    
    path_proj = Path(dir_proj)
