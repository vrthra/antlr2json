import random

def unify_key(grammar, key):
    return unify_rule(grammar, random.choice(grammar[key])) if key in grammar else [key]

def unify_rule(grammar, rule):
    return sum([unify_key(grammar, token) for token in rule], [])

import sys
import json

def main(arg):
    with open(arg) as f:
        g = json.load(fp=f)
    for i in range(10):
        v = unify_key(g, '<json>')
        print(''.join(v))

if __name__ == '__main__':
    main(sys.argv[1])
