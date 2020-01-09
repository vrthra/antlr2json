#!/usr/bin/env python
import fuzzingbook
import sys
import json

from fuzzingbook.Parser import IterativeEarleyParser as IEP


def main(fgrammar, finput):
    with open(fgrammar) as f:
       fg = json.load(fp=f) 
    with open(finput) as f:
        fin = f.read()

    grammar = fg['[grammar]']
    start = fg['[start]']
    p = IEP({}, start_symbol=start)
    p.cgrammar = grammar
    res = p.parse(fin)
    for t in res:
        print(t)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
