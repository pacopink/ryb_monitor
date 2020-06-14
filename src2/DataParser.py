#!/usr/bin/env python

import re 

r = re.compile(r'^(\s*)(.*)$')

def parse_line(line):
    l = line
    m = r.match(l)
    if m is None:
        return None
    ms = m.groups()
    return (len(ms[0]), ms[1])

FILE='data.out'
with open(FILE, 'r') as f:
    for l in f:
        print parse_line(l)



