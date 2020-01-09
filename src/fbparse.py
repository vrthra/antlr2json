#!/usr/bin/env python
import fuzzingbook
import sys
import json

from fuzzingbook.Parser import IterativeEarleyParser as IEP
#from fuzzingbook.Parser import PEGParser as IEP

def non_canonical(grammar):
    new_grammar = {}
    for k in grammar:
        rules = grammar[k]
        new_rules = []
        for rule in rules:
            new_rules.append(''.join(rule))
        new_grammar[k] = new_rules
    return new_grammar

def main(fgrammar, finput):
    with open(fgrammar) as f:
       fg = json.load(fp=f) 
    with open(finput) as f:
        fin = f.read()

    grammar = fg['[grammar]']
    start = fg['[start]']
    g = non_canonical(grammar)
    p = IEP(g, start_symbol=start, log=True)
    res = p.parse(fin)
    for t in res:
        print(t)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
