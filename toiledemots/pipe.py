#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import select

def fetch_text_lines(filename=None):
    """
    """

    if (filename and 
        os.path.exists(filename)):
        file = open(filename,'r')
    elif select.select([sys.stdin,],[],[],0.0)[0]:
        file = sys.stdin
    else:
        raise IOError("No data given as input")

    try:
        return [unicode(line,'utf-8') for line in iter(file.readline,'')]
    except UnicodeDecodeError as error:
        return [unicode(line,'latin1') for line in iter(file.readline,'')]
#    return [line for line in iter(file.readline,'')]

#    return [line.strip("\n").decode('windows-1252').encode('utf8') for line in iter(file.readline,'')]

if __name__=="__main__":
    if len(sys.argv) > 1:
        lines = fetch_text_lines(sys.argv[1])
    else:
        lines = fetch_text_lines()

    for i, line in enumerate(lines):
        print " %i : %s " % (i, line)
