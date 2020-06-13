#!/usr/bin/env python
#coding: utf-8

import sys
import getopt

opts, args = getopt.getopt(sys.argv[1:], "e:t:o:h", ["help", "output="])#"ho:"也可以写成'-h-o:'
print opts
print args
