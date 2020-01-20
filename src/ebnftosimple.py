import codecs
import string
RE_DEFS = {}

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
       if cmd == ['<skip>'] or cmd == [['<channel>', '<HIDDEN>']]:
           payload = jr[2]
           if payload[0] == 'seq':
              for tok in payload[1]:
                  t = convert_token(tok, g, k)
                  if t is not None:
                      tokens.append(t)
              g.setdefault('<>', []).append([k])
              return tokens
           assert False
       elif cmd == [['<channel>', '<ERROR>']]:
           return None
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
        if r is not None:
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
    assert res is not None
    jval[sym] = [[res, sym], [res]]
    return sym

def process_star(regex, jval, k):
    sym = '<_%s_STAR_%s>' % (k, next_sym())
    res = process_re(regex, jval, k)
    assert res is not None
    jval[sym] = [[res, sym], []]
    return sym

def process_q(regex, jval, k):
    sym = '<_%s_Q_%s>' % (k, next_sym())
    res = process_re(regex, jval, k)
    assert res is not None
    jval[sym] = [[res], []]
    return sym

def process_dot(values, jval, k):
    # dot is like OR but there is only one
    sym = '<_DOT>'
    jval[sym] = [[v] for v in string.printable]
    return sym


def process_OR(values, jval, k):
    sym = '<_%s_OR_%s>' % (k, next_sym())
    resl = []
    for v in values:
        res = process_re(v, jval, k)
        assert res is not None
        resl.append([res])
    jval[sym] = resl
    return sym

def process_NOT(regex, jval, k):
    if len(regex) == 1:
        sym = '<_%s_CNOT0_%s>' % (k, next_sym())
        # this is a set element. so treat it like one.
        assert len(regex) == 1
        jval[sym] = [[v] for v in string.printable if v != regex[0]]
        return sym

    op, val = regex
    if op == 'charset':
        chars = process_CHARSET(val, jval, k)
        # what is our full set of chars?
        our_chars = set(string.printable)
        rest = list(our_chars - set(chars))

        sym = '<_%s_CNOT_%s>' % (k, next_sym())
        jval[sym] = [[i] for i in rest]
        return sym
    elif op == 'seq':
        return process_SEQ(val, jval, k)
    else:
        assert False

def process_SEQ(regex, jval, k):
    sym = '<_%s_SEQ_%s>' % (k, next_sym())
    resl = []
    for e in regex:
        res = process_re(e, jval, k)
        if res is not None: # res is None when it is an action
            resl.append(res)
    jval[sym] = [resl]
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
    elif s[0] == 'charrange':
        return process_range(s[1], s[2], k)
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

def readjs(arg):
    with open(arg) as f:
        return json.load(fp=f)

import json

def main_no_lex(arg):
    with open(arg) as f:
        js = json.load(fp=f)
    start = js['[start]']
    grammar = js['[grammar]']
    assert js['[kind]'] == 'Both'
    return start, grammar

def main_with_lex(lexerarg, parserarg):
    ljs = readjs(lexerarg)
    assert ljs['[kind]'] == 'Lexer'
    pjs = readjs(parserarg)
    assert pjs['[kind]'] == 'Parser'
    start = pjs['[start]']
    grammar = dict(ljs['[grammar]'])
    grammar.update(**pjs['[grammar]'])
    return start, grammar

def main(args):
    if len(args) == 1:
        start, grammar = main_no_lex(args[0])
    elif len(args) == 2:
        start, grammar = main_with_lex(args[0], args[1])
    jval = convert_grammar(grammar)
    # now insert the skipped values.
    if '<>' in jval:
        jval = insert_skips(jval)
        jval['<>'].append(['<>','<>']) # zero or more
        jval['<>'].append([]) # zero or more
    jval['<EOF_sp_>'] = [['<>']]

    print(json.dumps({'[start]': start, '[grammar]': show_grammar(jval, start_symbol=start)}))

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
