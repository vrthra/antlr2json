def recurse_grammar(grammar, key, order):
    rules = sorted(grammar[key])
    old_len = len(order)
    for rule in rules:
        for token in rule:
            if token.startswith('<') and token.endswith('>'):
                if token not in order:
                    order.append(token)
    new = order[old_len:]
    for ckey in new:
        recurse_grammar(grammar, ckey, order)

def show_grammar(grammar, start_symbol='<START>'):
    order = [start_symbol]
    recurse_grammar(grammar, start_symbol, order)
    return {k: sorted(grammar[k]) for k in order}

import json
def main(gf):
    with open(gf) as f:
        j = json.load(fp=f)
    v = show_grammar(j['[grammar]'], start_symbol=j['[start]'])
    j['[grammar]'] = v
    print(json.dumps(j))

import sys
if __name__ == '__main__':
    main(sys.argv[1])
