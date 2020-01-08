import codecs
import string
RE_DEFS = {}

Counter = 0
def next_sym():
    global Counter
    r = Counter
    Counter += 1
    return str(r)

def convert_regex(jt, g):
    # RE_DEFS[key] = jt
    v = process_re(jt, g)
    if v is None:
        return None
    key = '<_re_%s>' % next_sym()
    g[key] = [[v]]
    return key

def convert_token(jt, g):
    if isinstance(jt, str):
        v = bytes(jt, 'utf-8').decode('unicode_escape')
        return v
    else:
        return convert_regex(jt, g)

def convert_rule(jr, k, g):
    tokens = []
    kind = jr[0]
    if kind == 'action':
       cmd = jr[1]
       if cmd == ['<skip>']:
           payload = jr[2]
           if payload[0] == 'seq':
              for tok in payload[1]:
                  t = convert_token(tok, g)
                  if t is not None:
                      tokens.append(t)
              g.setdefault('<>', []).append([k])
              return tokens
           assert False
       else:
          assert False
    elif kind == 'seq':
        for tok in jr[1]:
            t = convert_token(tok, g)
            if t is not None:
                tokens.append(t)
        return tokens

def convert_define(k, jd, g):
    rules = []
    for rule in jd:
        r = convert_rule(rule, k, g)
        rules.append(r)
    return rules

def convert_grammar(jg):
    res = {}
    for k in jg:
        v = convert_define(k, jg[k], res)
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

def process_dot(values, jval):
    # dot is like OR but there is only one
    k = '<_DOT>'
    jval[k] = [[v] for v in string.printable]
    return k


def process_OR(values, jval):
    k = '<_OR_%s>' % next_sym()
    jval[k] = [[process_re(v, jval)] for v in values]
    return k

def process_NOT(regex, jval):
    k = '<_NOT_%s>' % next_sym()
    op, val = regex
    assert op == 'charset'
    #res = process_re(regex, jval)
    chars = process_CHARSET(val, jval)
    # what is our full set of chars?
    our_chars = set(string.printable)
    rest = list(our_chars - set(chars))

    k = '<_CNOT_%s>' % next_sym()
    jval[k] = [[i] for i in rest]
    return k

def process_SEQ(regex, jval):
    k = '<_SEQ_%s>' % next_sym()
    res = [process_re(e, jval) for e in regex]
    jval[k] = [res]
    return k

def process_sqbr(val, jval):
    k = '<_CSET_%s>' % next_sym()
    s = process_CHARSET(val, jval)
    jval[k] = [[i] for i in s]
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
    return chars

def process_range(a, b):
    return ''.join([chr(c) for c in range(ord(a), ord(b)+1)])

def process_re(regex, jval):
    # return of process_re will be a token
    if isinstance(regex, str): return regex
    s = regex
    l = len(regex)
    if s[0] == 'action':
        # antlr parse actions are ignored as they are in
        # specific programming languages.
        return None
    if l < 2 or l > 2:
        assert False
        s = process_SEQ(regex, jval)
    else:
        op, val = regex
        # note there could be `?` to indicate nongreed on op[1]
        if op[0] == '*':
            s = process_star(val, jval)
        elif op[0] == '+':
            s = process_plus(val, jval)
        elif op[0] == '?':
            s = process_q(val, jval)
        elif op == 'dot':
            s = process_dot(val, jval)
        elif op == 'or':
            s = process_OR(val, jval)
        elif op == 'not':
            s = process_NOT(val, jval)
        elif op == 'seq':
            s = process_SEQ(val, jval)
        elif op == 'charset':
            assert (val[0], val[-1]) == ('[', ']')
            mystring = val[1:-1]
            v = bytes(mystring, 'utf-8').decode('unicode_escape')
            #v = codecs.escape_decode(bytes(mystring, "utf-8"))[0].decode("utf-8")
            s = process_sqbr(v, jval)
        else:
            assert False
            # this is a seq.
            s = process_SEQ(regex, jval)
    return s

def insert_skip_in_rule(rule_):
    # before ach Lexer token, insert '<>'
    tokens = []
    for t in rule_:
        if len(t) > 1 and t[0] == '<' and t[1].isupper():
            tokens.append('<>')
        tokens.append(t)
    return tokens

def insert_skips(g):
    new_g = {}
    for k in g:
        new_rules = []
        for rule_ in g[k]:
            if k != '<>':
                rule = insert_skip_in_rule(rule_)
            else:
                rule = rule_
            new_rules.append(rule)
        new_g[k] = new_rules
    return new_g


def main(arg):
    import json
    with open(arg) as f:
        js = json.load(fp=f)
    start = js['']
    del js['']

    jval = convert_grammar(js)
    # now insert the skipped values.
    if '<>' in jval:
        jval = insert_skips(jval)

    jval[''] = start
    print(json.dumps(jval))

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
