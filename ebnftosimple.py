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
    k = '<_OR_%s>' % next_sym()
    jval[k] = [[process_re(v, jval)] for v in values]
    return k

def process_NOT(regex, jval):
    k = '<_NOT_%s>' % next_sym()
    res = process_re(regex, jval)
    jval[k] = [['NOT', res]]
    return k

def process_SEQ(regex, jval):
    k = '<_SEQ_%s>' % next_sym()
    res = [process_re(e, jval) for e in regex]
    jval[k] = [res]
    return k

def process_CHARSET(val, jval):
    #now get everything until the first range
    v = val.find('-')
    if v == -1:
        return process_chars(val)
    else:
        if v == len(val) -1: # last is not special char
            return process_chars(val)
        else:
            first_part = val[:v-1] # v-1 is the start char of range
            # v + 1 is the end char of range
            return process_chars(first_part) + process_range(val[v-1], val[v+1]) + process_CHARSET(val[v+2:], jval)

def process_chars(chars):
    return '[%s]' % chars

def process_range(a, b):
    return '[%s-%s]' % (a, b)

def process_re(regex, jval):
    # return of process_re will be a token
    if isinstance(regex, str): return regex
    s = regex
    if len(regex) < 2:
        s = process_SEQ(regex, jval)
    else:
        op, val = regex
        if op == '*':
            s = process_star(val, jval)
        elif op == '+':
            s = process_plus(val, jval)
        elif op == '?':
            s = process_q(val, jval)
        elif op == 'or':
            s = process_OR(val, jval)
        elif op == 'not':
            s = process_NOT(val, jval)
        elif op == 'charset':
            assert (val[0], val[-1]) == ('[', ']')
            v = bytes(val[1:-1], 'utf-8').decode('unicode_escape')
            s = process_CHARSET(v, jval)
        else:
            # this is a seq.
            s = process_SEQ(regex, jval)
    return s

def main(arg):
    import json
    with open(arg) as f:
        js = json.load(fp=f)

    jval = convert_grammar(js)
    for k in RE_DEFS:
        # return of process_re will be a token
        v = process_re(RE_DEFS[k], jval)
        jval[k] = [[v]]

    #for k in jval:
    #    print(k)
    #    for r in jval[k]:
    #        print('  ', r)
    print(json.dumps(jval))

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
