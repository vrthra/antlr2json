def convert_token(jt):
    return jt

def convert_rule(jr):
    tokens = []
    for tok in jr:
        t = convert_token(tok)
        tokens.append(tok)
    return tokens

def convert_define(k, jd):
    rules = []
    for rule in jd:
        r = convert_rule(rule)
        rules.append(r)
    return rules

def convert_grammar(jg):
    res = {}
    for k in jg:
        v = convert_define(k, jg[k])
        res[k] = v
    return res

def main(arg):
    import json
    with open(arg) as f:
        js = json.load(fp=f)

    jval = convert_grammar(js)
    for k in jval:
        print(k)
        for r in jval[k]:
            print('  ', r)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
