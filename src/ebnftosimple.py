import codecs
import string
RE_DEFS = {}

Counter = 0
def next_sym():
    global Counter
    r = Counter
    Counter += 1
    return str(r)

def convert_regex(jt, g, k):
    v = process_re(jt, g, k)
    if v is None:
        return None
    sym = '<_%s_re_%s>' % (k, next_sym())
    g[sym] = [[v]]
    return sym

def convert_token(jt, g, k):
    if isinstance(jt, str):
        v = bytes(jt, 'utf-8').decode('unicode_escape')
        return v
    else:
        return convert_regex(jt, g, k[1:-1])

def convert_rule(jr, k, g):
    tokens = []
    kind = jr[0]
    if kind == 'action':
       cmd = jr[1]
       if cmd == ['<skip>']:
           payload = jr[2]
           if payload[0] == 'seq':
              for tok in payload[1]:
                  t = convert_token(tok, g, k)
                  if t is not None:
                      tokens.append(t)
              g.setdefault('<>', []).append([k])
              return tokens
           assert False
       else:
          assert False
    elif kind == 'seq':
        for tok in jr[1]:
            t = convert_token(tok, g, k)
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

def process_plus(regex, jval, k):
    sym = '<_%s_PLUS_%s>' % (k, next_sym())
    res = process_re(regex, jval, k)
    jval[sym] = [[res, sym], [res]]
    return sym

def process_star(regex, jval, k):
    sym = '<_%s_STAR_%s>' % (k, next_sym())
    res = process_re(regex, jval, k)
    jval[sym] = [[res, sym], []]
    return sym

def process_q(regex, jval, k):
    sym = '<_%s_Q_%s>' % (k, next_sym())
    res = process_re(regex, jval, k)
    jval[sym] = [[res], []]
    return sym

def process_dot(values, jval, k):
    # dot is like OR but there is only one
    sym = '<_DOT>'
    jval[sym] = [[v] for v in string.printable]
    return sym


def process_OR(values, jval, k):
    sym = '<_%s_OR_%s>' % (k, next_sym())
    jval[sym] = [[process_re(v, jval, k)] for v in values]
    return sym

def process_NOT(regex, jval, k):
    op, val = regex
    assert op == 'charset'
    chars = process_CHARSET(val, jval, k)
    # what is our full set of chars?
    our_chars = set(string.printable)
    rest = list(our_chars - set(chars))

    sym = '<_%s_CNOT_%s>' % (k, next_sym())
    jval[sym] = [[i] for i in rest]
    return sym

def process_SEQ(regex, jval, k):
    sym = '<_%s_SEQ_%s>' % (k, next_sym())
    res = [process_re(e, jval, k) for e in regex]
    jval[sym] = [res]
    return sym

def process_sqbr(val, jval, k):
    sym = '<_%s_CSET_%s>' % (k, next_sym())
    s = process_CHARSET(val, jval, k)
    jval[sym] = [[i] for i in s]
    return sym

def process_CHARSET(val, jval, k):
    #now get everything until the first range
    v = val.find('-')
    if v == -1:
        return process_chars(val, k)
    else:
        if v == len(val) -1: # last is not special char
            return process_chars(val, k)
        else:
            first_part = val[:v-1] # v-1 is the start char of range
            # v + 1 is the end char of range
            return process_chars(first_part, k) + \
                    process_range(val[v-1], val[v+1], k) +\
                    process_CHARSET(val[v+2:], jval, k)

def process_chars(chars, k):
    return chars

def process_range(a, b, k):
    return ''.join([chr(c) for c in range(ord(a), ord(b)+1)])

def process_re(regex, jval, k):
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
        s = process_SEQ(regex, jval, k)
    else:
        op, val = regex
        # note there could be `?` to indicate nongreed on op[1]
        if op[0] == '*':
            s = process_star(val, jval, k)
        elif op[0] == '+':
            s = process_plus(val, jval, k)
        elif op[0] == '?':
            s = process_q(val, jval, k)
        elif op == 'dot':
            s = process_dot(val, jval, k)
        elif op == 'or':
            s = process_OR(val, jval, k)
        elif op == 'not':
            s = process_NOT(val, jval, k)
        elif op == 'seq':
            s = process_SEQ(val, jval, k)
        elif op == 'charset':
            assert (val[0], val[-1]) == ('[', ']')
            mystring = val[1:-1]
            v = bytes(mystring, 'utf-8').decode('unicode_escape')
            #v = codecs.escape_decode(bytes(mystring, "utf-8"))[0].decode("utf-8")
            s = process_sqbr(v, jval, k)
        else:
            assert False
            # this is a seq.
            s = process_SEQ(regex, jval, k)
    return s

def insert_skip_in_rule(rule_):
    # before ach Lexer token, insert '<>'
    tokens = []
    for t in rule_:
        if len(t) > 1 and t[0] == '<' and t[1].isupper():
            tokens.append('<>')
        tokens.append(t)
    return tokens

def add_sp_to_define(rules):
    nrs = []
    for r in rules:
        nr = []
        for t in r:
            if (t[0], t[-1]) != ('<', '>'): # terminal
                nr.append('<>')
                nr.append(t)
            else:
                if not t[1].isupper(): # parser
                    nr.append(t)
                else:
                    nr.append('<%s_sp_>' % t[1:-1])
        nrs.append(nr)
    return nrs

def replace_lexer(g):
    ng = {}
    for k in g:
        nrs = []
        # it this is already a lexical token, we don't want
        # to mess with internal stuff.
        if k[1].isupper():
            nrs = g[k]
        elif (k[0], k[1]) == ('<', '>'):
            nrs = g[k]
        elif k[1] == '_':
            # if the RE is part of parser, we want to insert
            # but if the RE is part of lexer, we dont want to
            # insert.
            if k[2].isupper(): # lexer
                nrs = g[k]
            else:
                nrs = add_sp_to_define(g[k])
        else:
            nrs = add_sp_to_define(g[k])
        ng[k] = nrs
    return ng

def insert_skips(g):
    # We first replace any Lexer term with Lexer_sp_
    # and add Lexer_sp_ = sp Lexer to the grammar.
    lexers = [k for k in g if k[1].isupper()]
    g = replace_lexer(g)
    for t in lexers:
        g['<%s_sp_>' % t[1:-1]] = [['<>', t]]
    return g


def main(arg):
    import json
    with open(arg) as f:
        js = json.load(fp=f)
    start = js['[start]']
    grammar = js['[grammar]']

    jval = convert_grammar(grammar)
    # now insert the skipped values.
    if '<>' in jval:
        jval = insert_skips(jval)

    print(json.dumps({'[start]': start, '[grammar]': jval}))

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
