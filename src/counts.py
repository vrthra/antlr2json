import sys
import json

def process_json(j):
    print('nonterminals', len(j.keys()))
    print('rules', len([r for k in j for r in j[k]]))
    terminals = []
    nonterminals = []
    for k in j:
        for r in j[k]:
            for t in r:
                if (t[0], t[-1]) == ('<','>'):
                    nonterminals.append(t)
                else:
                    terminals.append(t)
    print('terminals', len(set(terminals)))
    print('check: nonterminals', len(set(nonterminals)))

with open(sys.argv[1]) as f:
    j = json.load(fp=f)
    process_json(j['[grammar]'])

