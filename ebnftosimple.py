RE_DEFS = {}

Counter = 0
def next_sym():
    global Counter
    r = Counter
    Counter += 1
    return str(r)

def convert_regex(jt):
    key = '<_re_%s>' % next_sym()
    RE_DEFS[key] = jt
    return key

def convert_token(jt):
    if isinstance(jt, str):
        return jt
    else:
        return convert_regex(jt)

def convert_rule(jr):
    tokens = []
    for tok in jr:
        t = convert_token(tok)
        tokens.append(t)
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

def process_plus(regex, jval):
    k = '<_PLUS_%s>' % next_sym()
    res = process_re(regex, jval)
    jval[k] = [[res, k], [res]]
    return k

def process_star(regex, jval):
    k = '<_STAR_%s>' % next_sym()
    res = process_re(regex, jval)
    jval[k] = [[res, k], []]
    return k

def process_q(regex, jval):
    k = '<_Q_%s>' % next_sym()
    res = process_re(regex, jval)
    jval[k] = [[res], []]
    return k

def process_OR(values, jval):
    k = '<_NOT_%s>' % next_sym()
    jval[k] = [[process_re(v, jval)] for v in values]
    return k

def process_NOT(regex, jval):
    k = '<_NOT_%s>' % next_sym()
    res = process_re(regex, jval)
    jval[k] = ['NOT', res]
    return k

def process_re(regex, jval):
    if isinstance(regex, str): return regex
    if len(regex) < 2: return regex
    op, val = regex
    if op == '*':
        return process_star(val, jval)
    elif op == '+':
        return process_plus(val, jval)
    elif op == '?':
        return process_q(val, jval)
    elif op == 'or':
        return process_OR(val, jval)
    elif op == 'not':
        return process_NOT(val, jval)
    else:
        return regex

def main(arg):
    import json
    with open(arg) as f:
        js = json.load(fp=f)

    jval = convert_grammar(js)
    for k in RE_DEFS:
        v = process_re(RE_DEFS[k], jval)
        jval[k] = [[v]]

    for k in jval:
        print(k)
        for r in jval[k]:
            print('  ', r)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
