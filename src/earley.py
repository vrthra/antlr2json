#!/usr/bin/env python
import fuzzingbook
import sys
import json

from fuzzingbook.Parser import IterativeEarleyParser as IEP
#from fuzzingbook.Parser import PEGParser as IEP
from fuzzingbook.Parser import nullable


def non_canonical(grammar):
    new_grammar = {}
    for k in grammar:
        rules = grammar[k]
        new_rules = []
        for rule in rules:
            new_rules.append(''.join(rule))
        new_grammar[k] = new_rules
    return new_grammar
#from fuzzingbook.Parser import PEGParser as IEP


def main(fgrammar, finput):
    with open(fgrammar) as f:
       fg = json.load(fp=f) 
    with open(finput) as f:
        fin = f.read()

    grammar = fg['[grammar]']
    nc_grammar = non_canonical(grammar)
    start = fg['[start]']
    p = IEP(nc_grammar, start_symbol=start, log=True)
    #p.cgrammar = grammar
    #p._grammar = grammar
    #p.epsilon = nullable(grammar)
    res = p.parse(fin)
    for t in res:
        print(t)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
