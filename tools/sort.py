#!/usr/bin/env python3.10
import sys
_in = sys.stdin.read()
lines = [ i.strip() for i in _in.splitlines() if i.strip() ]
sorted_args = sorted(lines)
for ln in sorted_args:
    print(ln)

sys.exit()