from antlr4 import *
from ANTLRv4Lexer import ANTLRv4Lexer
from ANTLRv4Parser import ANTLRv4Parser
import sys
import copy

EBNF = {}
Counter = 0

def nxt_sym(prefix):
    global Counter
    r = Counter
    Counter += 1
    return '%s_%d' % (prefix, r)


class AntlrG:
    def __init__(self, code):
        self.lexer = ANTLRv4Lexer(InputStream(code))

        tokenStream = CommonTokenStream(self.lexer)
        self.parser = ANTLRv4Parser(tokenStream)
        self.parser.buildParseTrees = True

        self.tree = self.parser.grammarSpec() # entry
        self.res = self.parse_grammarSpec(self.tree)

    def _parse_token(self, children, typ):
        assert isinstance(children[0], tree.Tree.TerminalNodeImpl)
        tok = children.pop(0)
        assert tok.symbol.type == typ
        return tok, children

    def _parse_object(self, children, typ):
        assert isinstance(children[0], typ)
        obj = children.pop(0)
        return obj, children

    def _parse_list(self, children, pred, atmost=-1, atleast=0):
        lst = []
        while children:
            if atmost == 0: break
            atmost -= 1
            if pred(children[0]):
                obj = children.pop(0)
                lst.append(obj)
            else:
                break
        assert len(lst) >= atleast
        return lst, children

    def _parse_question(self, children, pred):
        return self._parse_list(children, pred, atmost=1) # a maximum of one

    def _parse_star(self, children, pred):
        return self._parse_list(children, pred)

    def _parse_star_object(self, children, typ):
        return self._parse_star(children, lambda x: isinstance(x, typ))

    def _parse_list_x(self, children, pred_inside, atmost=-1):
        # eat children in chunks
        res = []
        while children:
            if atmost == 0: break
            atmost -= 1
            _children = copy.copy(children)
            _o, _remaining = pred_inside(_children)
            if _o is None: break # children is not touched
            children = _remaining
            res.append(_o)
        return res, children

    def _parse_question_x(self, children, pred_inside):
        return self._parse_list_x(children, pred_inside, atmost=1)

    def _parse_star_x(self, children, pred_inside):
        return self._parse_list_x(children, pred_inside)


    def _parse_star_token(self, children, typ):
        return self._parse_list(children, lambda x: isinstance(x, tree.Tree.TerminalNodeImpl) and x.symbol.type == typ)

    def _parse_question_object(self, children, typ):
        return self._parse_question(children, lambda x: isinstance(x, typ))

    def _parse_question_token(self, children, typ):
        return self._parse_question(children, lambda x: isinstance(x, tree.Tree.TerminalNodeImpl) and x.symbol.type == typ)

    def parse_grammarSpec(self, parsedtree):
        '''
        grammarSpec
           : DOC_COMMENT* grammarDecl prequelConstruct* rules modeSpec* EOF
           ;
        '''
        children = copy.copy(parsedtree.children)
        # if there are doc_comments, skip them first
        _o, children = self._parse_star_token(children, self.lexer.DOC_COMMENT)
        self.parse_DOC_COMMENT_star(_o)

        _o, children = self._parse_object(children, ANTLRv4Parser.GrammarDeclContext)
        self.parse_grammarDecl(_o)

        _o, children = self._parse_star_object(children, ANTLRv4Parser.PrequelConstructContext)
        self.parse_prequelConstruct_star(_o)

        rules, children = self._parse_object(children, ANTLRv4Parser.RulesContext)
        rules_json = self.parse_rules(rules)

        _o, children = self._parse_star_object(children, ANTLRv4Parser.ModeSpecContext)
        self.parse_modeSpec_star(_o)

        _o, children = self._parse_token(children, self.parser.EOF)
        self.parse_EOF(_o)
        return rules_json
        #tree.toStringTree(recog=self.parser)

    def parse_LEXER_CHAR_SET(self, obj):
        return obj.symbol.text

    def parse_COMMA(self, obj):
        assert obj.symbol.text == ','
        return ','

    def parse_QUESTION(self, obj):
        assert obj.symbol.text == '?'
        return '?'

    def parse_STAR(self, obj):
        assert obj.symbol.text == '*'
        return '*'

    def parse_PLUS(self, obj):
        assert obj.symbol.text == '+'
        return '+'

    def parse_NOT(self, obj):
        assert obj.symbol.text == '~'
        return '~'

    def parse_RARROW(self, obj):
        assert obj.symbol.text == '->'
        return '->'

    def parse_LPAREN(self, obj):
        assert obj.symbol.text == '('
        return '('

    def parse_RPAREN(self, obj):
        assert obj.symbol.text == ')'
        return ')'

    def parse_EOF(self, obj):
        assert obj.symbol.text == '<EOF>'
        return None

    def parse_prequelConstruct_star(self, obj): return None

    def parse_prequelConstruct(self, obj):
        '''
        prequelConstruct
           : optionsSpec
           | delegateGrammars
           | tokensSpec
           | channelsSpec
           | action_
           ;
        '''
        return None

    def parse_DOC_COMMENT_star(self, o): return None

    def parse_modeSpec_star(self, children): return None

    def parse_grammarDecl(self, children):
        # SKIPPED
        '''
        grammarDecl
           : grammarType identifier SEMI
           ;
        '''
        return None

    def parse_rulesSpec_star(self, ruleSpec_star):
        rules_json = []
        for rule in ruleSpec_star:
            o = self.parse_ruleSpec(rule)
            rules_json.append(o)

        return rules_json

    def parse_ruleSpec(self, ruleSpec):
        '''
        ruleSpec
           : parserRuleSpec
           | lexerRuleSpec
           ;
        '''
        children = ruleSpec.children
        assert len(children) == 1
        rspec = children[0]
        if isinstance(rspec, ANTLRv4Parser.ParserRuleSpecContext):
            return self.parse_parserRuleSpec(rspec)
        elif isinstance(rspec, ANTLRv4Parser.LexerRuleSpecContext):
            return self.parse_lexerRuleSpec(rspec)
        else:
            assert False

    def parse_parserRuleSpec(self, rspec):
        '''
        parserRuleSpec
           : DOC_COMMENT* ruleModifiers? RULE_REF argActionBlock? ruleReturns? throwsSpec? localsSpec? rulePrequel* COLON ruleBlock SEMI exceptionGroup
           ;
        '''
        defines = None
        children = copy.copy(rspec.children)
        # parse and ignore
        _o, children = self._parse_star_token(children, self.lexer.DOC_COMMENT)
        self.parse_DOC_COMMENT_star(_o)

        _o, children = self._parse_question_object(children, ANTLRv4Parser.RuleModifiersContext) # a maximum of one
        self.parse_ruleModifiers_question(_o)

        _o, children = self._parse_token(children, self.lexer.RULE_REF)
        rule_name = self.parse_RULE_REF(_o)

        _o, children = self._parse_question_object(children, ANTLRv4Parser.ArgActionBlockContext)
        _o, children = self._parse_question_object(children, ANTLRv4Parser.RuleReturnsContext)
        _o, children = self._parse_question_object(children, ANTLRv4Parser.ThrowsSpecContext)
        _o, children = self._parse_question_object(children, ANTLRv4Parser.LocalsSpecContext)
        _o, children = self._parse_star_object(children, ANTLRv4Parser.RulePrequelContext)

        _o, children = self._parse_token(children, self.lexer.COLON)
        _o, children = self._parse_object(children, ANTLRv4Parser.RuleBlockContext)
        defines = self.parse_ruleBlock(_o)

        _o, children = self._parse_token(children, self.lexer.SEMI)
        _o, children = self._parse_object(children, ANTLRv4Parser.ExceptionGroupContext)

        return [rule_name, defines]


    def parse_ruleBlock(self, rb):
        '''
        ruleBlock
           : ruleAltList
           ;
        '''
        # a define with multiple rules
        _o, children = self._parse_object(copy.copy(rb.children), ANTLRv4Parser.RuleAltListContext)
        assert not children
        return self.parse_ruleAltList(_o)

    def parse_ruleAltList(self, ral):
        '''
        ruleAltList
           : labeledAlt (OR labeledAlt)*
           ;
        '''
        # a define with multiple rules
        def pred_inside(children):
            _o, children = self._parse_question_token(children, self.lexer.OR)
            if _o is None: return None
            _o, children = self._parse_object(children, ANTLRv4Parser.LabeledAltContext)

            # labeledAlt can be empty TODO.
            assert _o is not None
            return _o, children

        children = copy.copy(ral.children)
        o = children.pop(0)
        lalt_children = [o]

        cs, children = self._parse_star_x(children, pred_inside)
        lalt_children.extend(cs)
        res = []
        for c in lalt_children:
            o = self.parse_labeledAlt(c)
            res.append(o)
        return res

    def parse_labeledAlt(self, obj):
        '''
        labeledAlt
           : alternative (POUND identifier)?
           ;
        '''
        # a single production rule
        def pred_inside(children_):
            _o, children = self._parse_question_token(children, self.lexer.POUND)
            if _o is None: return None
            _o, children = self._parse_object(children, ANTLRv4Parser.IdentifierContext)
            assert _o is not None
            return _o, children

        children = obj.children
        ac, children = self._parse_object(children, ANTLRv4Parser.AlternativeContext)
        acr =  self.parse_alternative(ac)
        res, children = self._parse_question_x(children, pred_inside)

        return acr


    def parse_alternative(self, obj):
        '''
        alternative
           : elementOptions? element+
           |
           // explicitly allow empty alts
           ;
        '''
        # a single production rule (or empty)
        children = obj.children
        if not children:
            return []
        _o, children = self._parse_question_object(children, ANTLRv4Parser.ElementOptionsContext)
        elts, children = self._parse_star_object(children, ANTLRv4Parser.ElementContext)
        assert len(elts) >= 1 # element+
        res = []
        for e in elts:
            r = self.parse_element(e)
            res.append(r)
        return res

    def parse_element(self, obj):
        '''
        element
           : labeledElement (ebnfSuffix |)
           | atom (ebnfSuffix |)
           | ebnf
           | actionBlock QUESTION?
           ;
        '''
        # a single token
        # By the fuzzingbook canonical format, this should return a single token
        # not an array. So we have to figure out what happens when there is an
        # ebnfSuffix
        children = copy.copy(obj.children)
        c = children[0]
        if isinstance(c, ANTLRv4Parser.LabeledElementContext):
            assert False
            le = self.parse_labeledElement(c)
            ebnf = None
            if len(children) > 1:
                ebnf = self.parse_ebnfSuffix(children[1])
                assert False
                # return [le, ebnf]
            return le
        elif isinstance(c, ANTLRv4Parser.AtomContext):
            le = self.parse_atom(c)
            ebnf = None
            if len(children) > 1:
                ebnf = self.parse_ebnfSuffix(children[1])
                assert False
                # return [le, ebnf]
            return le
        elif isinstance(c, ANTLRv4Parser.EbnfContext):
            blk, blksuffix = self.parse_ebnf(c)
            #sym = '<%s_%s>' % (nxt_sym('element'), blksuffix)
            #EBNF[sym] = [blk, blksuffix]
            #return sym
            return (blksuffix, blk)

        elif isinstance(c, ANTLRv4Parser.ActionBlockContext):
            raise NotImplemented()
        else:
            assert False

    def parse_setElement(self, obj):
        '''
        setElement
           : TOKEN_REF elementOptions?
           | STRING_LITERAL elementOptions?
           | characterRange
           | LEXER_CHAR_SET
           ;
        '''
        children = copy.copy(obj.children)
        c = children.pop(0)
        if isinstance(c, tree.Tree.TerminalNodeImpl):
            if c.symbol.type == self.lexer.TOKEN_REF:
                assert not children
                return self.parse_TOKEN_REF(c)
            elif c.symbol.type == self.lexer.STRING_LITERAL:
                assert not children
                return self.parse_STRING_LITERAL(c)
            elif c.symbol.type == self.lexer.LEXER_CHAR_SET:
                assert not children
                return self.parse_LEXER_CHAR_SET(c)
            else:
                assert False

        elif isinstance(c, ANTLRv4Parser.CharacterRangeContext):
            assert not children
            return self.parse_characterRange(c)
        else:
            assert False

    def parse_ebnf(self, obj):
        '''
        ebnf
           : block blockSuffix?
           ;
        '''
        children = copy.copy(obj.children)
        _o, children = self._parse_object(children, ANTLRv4Parser.BlockContext)
        v = self.parse_block(_o)

        _o, children = self._parse_question_object(children, ANTLRv4Parser.BlockSuffixContext)
        if _o:
            v1 = self.parse_blockSuffix(_o[0])
            # v1 could be *, +, ?, *?, +?, or ??
            return [v, v1]
        assert False
        return [v, None]

    def parse_blockSuffix(self, obj):
        '''
        blockSuffix
           : ebnfSuffix
           ;
        '''
        children = obj.children
        _o, children = self._parse_object(children, ANTLRv4Parser.EbnfSuffixContext)
        assert not children
        return self.parse_ebnfSuffix(_o)

    def parse_ebnfSuffix(self, obj):
        '''
        ebnfSuffix
           : QUESTION QUESTION?
           | STAR QUESTION?
           | PLUS QUESTION?
           ;
        '''
        children = copy.copy(obj.children)
        c = children.pop(0)
        assert not children # How to handle ?? or *? or +?
        assert isinstance(c, tree.Tree.TerminalNodeImpl)
        if c.symbol.type == self.lexer.QUESTION:
            v = self.parse_QUESTION(c)
            _o, children = self._parse_question_token(children, self.lexer.QUESTION)
            return v + ''.join([self.parse_QUESTION(i) for i in _o])
        elif c.symbol.type == self.lexer.STAR:
            v = self.parse_STAR(c)
            _o, children = self._parse_question_token(children, self.lexer.QUESTION)
            return v + ''.join([self.parse_QUESTION(i) for i in _o])
        elif c.symbol.type == self.lexer.PLUS:
            v = self.parse_PLUS(c)
            _o, children = self._parse_question_token(children, self.lexer.QUESTION)
            return v + ''.join([self.parse_QUESTION(i) for i in _o])
        else:
            assert False

    def parse_block(self, obj):
        '''
        block
           : LPAREN (optionsSpec? ruleAction* COLON)? altList RPAREN
        ;
        '''
        children = copy.copy(obj.children)
        _o, children = self._parse_token(children, self.lexer.LPAREN)

        def pred_inside(children_):
            children = copy.copy(children_)
            _o1, children = self._parse_question_object(children, ANTLRv4Parser.OptionsSpecContext)
            assert not _o1
            _o2, children = self._parse_star_object(children, ANTLRv4Parser.RuleActionContext)
            assert not _o2
            _o3, children = self._parse_question_token(children, self.lexer.COLON)
            if not _o3:
                return None, children_
            o = _o3[0]
            return o, children

        res, children = self._parse_question_x(children, pred_inside)
        assert not res
        altlst, children = self._parse_object(children, ANTLRv4Parser.AltListContext)
        _o, children = self._parse_token(children, self.lexer.RPAREN)
        res = self.parse_altList(altlst)
        return res

    def parse_altList(self, obj):
        '''
        altList
           : alternative (OR alternative)*
           ;
        '''
        children = copy.copy(obj.children)
        alt, children = self._parse_object(children, ANTLRv4Parser.AlternativeContext)

        # a single production rule
        def pred_inside(children):
            _o, children = self._parse_question_token(children, self.lexer.OR)
            if _o is None: return None
            _o, children = self._parse_object(children, ANTLRv4Parser.AlternativeContext)
            assert _o is not None
            return _o, children

        alts, children = self._parse_star_x(children, pred_inside)
        altlst = [alt]  + alts
        res = []
        for a in altlst:
            r = self.parse_alternative(a)
            res.append(r)
        return ('or', res)

    def parse_atom(self, obj):
        '''
        atom
           : terminal
           | ruleref
           | notSet
           | DOT elementOptions?
           ;
        '''
        # A single token -- can be a terminal or a nonterminal
        children = obj.children
        c = children[0]
        if isinstance(c, ANTLRv4Parser.TerminalContext):
            # note: this may simply be a parser terminal. It does
            # not mean that it is a lexer terminal
            return self.parse_terminal(c)
        elif isinstance(c, ANTLRv4Parser.RulerefContext):
            return self.parse_ruleref(c)
        elif isinstance(c, ANTLRv4Parser.NotSetContext):
            return self.parse_notSet(c)
        else:
            assert isinstance(c, tree.Tree.TerminalNodeImpl)
            raise NotImplemented()

    def parse_notSet(self, obj):
        '''
        notSet
           : NOT setElement
           | NOT blockSet
           ;
        '''
        children = copy.copy(obj.children)
        _o, children = self._parse_token(children, self.lexer.NOT)
        self.parse_NOT(_o)
        c = children.pop(0)
        assert not children
        if isinstance(c, ANTLRv4Parser.SetElementContext):
            v = self.parse_setElement(c)
            return ('not', v)
        elif isinstance(c, ANTLRv4Parser.BlockSetContext):
            v = self.parse_blockSet(c)
            return ('not', v)
        else: assert False

    def parse_terminal(self, obj):
        '''
        terminal
           : TOKEN_REF elementOptions?
           | STRING_LITERAL elementOptions?
           ;
        '''
        children = copy.copy(obj.children)
        c = children.pop(0)
        assert isinstance(c, tree.Tree.TerminalNodeImpl)
        if c.symbol.type == self.lexer.TOKEN_REF:
            v = self.parse_RULE_REF(c)
            _o, children = self._parse_question_object(children, ANTLRv4Parser.ElementOptionsContext)
            assert not _o
            return v
        elif c.symbol.type == self.lexer.STRING_LITERAL:
            v = self.parse_STRING_LITERAL(c)
            _o, children = self._parse_question_object(children, ANTLRv4Parser.ElementOptionsContext)
            assert not _o
            return v
        else:
            assert False

    def parse_STRING_LITERAL(self, obj):
        v = obj.symbol.text
        assert (v[0], v[-1]) == ("'","'")
        return v[1:-1]

    def parse_ruleref(self, obj):
        '''
        ruleref
           : RULE_REF argActionBlock? elementOptions?
           ;
        '''
        children = obj.children
        _o, children = self._parse_token(children, self.lexer.RULE_REF)
        v = self.parse_RULE_REF(_o)
        _o, children = self._parse_question_object(children, ANTLRv4Parser.ArgActionBlockContext)
        assert not _o
        _o, children = self._parse_question_object(children, ANTLRv4Parser.ElementOptionsContext)
        assert not _o
        assert not children
        return v

    def parse_labeledElement(self, obj):
        '''
        labeledElement
           : identifier (ASSIGN | PLUS_ASSIGN) (atom | block)
           ;
        '''
        children = copy.copy(obj.children)
        _o, children = self._parse_object(children, ANTLRv4Parser.IdentifierContext)
        o = self.parse_identifier(_o)
        assign = children.pop(0)
        assert isinstance(assign, tree.Tree.TerminalNodeImpl)
        nxt = children.pop(0)
        res = None
        if isinstance(nxt, ANTLRv4Parser.AtomContext):
            res = self.parse_atom(nxt)
        elif isinstance(nxt, ANTLRv4Parser.BlockContext):
            assert False
            res = self.parse_block(nxt)
        else:
            assert False
        assert not children
        return [o, res]

    def parse_identifier(self, obj):
        '''
        identifier
           : RULE_REF
           | TOKEN_REF
           ;
        '''
        children = obj.children
        assert len(children) == 1
        c = children[0]
        assert isinstance(c, tree.Tree.TerminalNodeImpl)
        if c.symbol.type == self.lexer.RULE_REF:
            return self.parse_RULE_REF(c)
        elif c.symbol.type == self.lexer.TOKEN_REF:
            return self.parse_TOKEN_REF(c)
        else:
            assert False

    def parse_RULE_REF(self, obj):
        v = obj.symbol.text
        return '<%s>' % v

    def parse_TOKEN_REF(self, obj):
        v = obj.symbol.text
        return '<%s>' % v

    def parse_ruleModifiers_question(self, objs):
        if not objs: return []
        assert len(objs) == 1
        return self.parse_ruleModifier(objs[0])

    def parse_ruleModifier(self, obj):
        '''
        ruleModifier
           : PUBLIC
           | PRIVATE
           | PROTECTED
           | FRAGMENT
           ;
        '''
        assert len(obj.children) == 1
        c = obj.children[0]
        if c.symbol.type == self.lexer.FRAGMENT: return self.parse_FRAGMENT(c)
        elif c.symbol.type == self.lexer.PRIVATE: return self.parse_PRIVATE(c)
        elif c.symbol.type == self.lexer.PUBLIC: return self.parse_PUBLIC(c)
        elif c.symbol.type == self.lexer.PROTECTED: return self.parse_PROTECTED(c)
        else: assert FALSE

    def parse_FRAGMENT(self, obj): return obj.symbol.text
    def parse_PUBLIC(self, obj): return obj.symbol.text
    def parse_PRIVATE(self, obj): return obj.symbol.text
    def parse_PROTECTED(self, obj): return obj.symbol.text

    def parse_FRAGMENT_question(self, objs):
        if not objs: return []
        assert len(objs) == 1
        return self.parse_FRAGMENT(objs[0])

    def parse_lexerRuleSpec(self, rspec):
        '''
        lexerRuleSpec
           : DOC_COMMENT* FRAGMENT? TOKEN_REF COLON lexerRuleBlock SEMI
           ;
        '''
        children = rspec.children
        _o, children = self._parse_star_token(children, self.lexer.DOC_COMMENT)
        self.parse_DOC_COMMENT_star(_o)

        _o, children = self._parse_question_token(children, self.lexer.FRAGMENT)
        self.parse_FRAGMENT_question(_o)

        _o, children = self._parse_token(children, self.lexer.TOKEN_REF)
        token_name = self.parse_TOKEN_REF(_o)

        _o, children = self._parse_token(children, self.lexer.COLON)

        _o, children = self._parse_object(children, ANTLRv4Parser.LexerRuleBlockContext)
        tdef = self.parse_lexerRuleBlock(_o)

        _o, children = self._parse_token(children, self.lexer.SEMI)

        return [token_name, tdef]

    def parse_lexerRuleBlock(self, obj):
        '''
        lexerRuleBlock
           : lexerAltList
           ;
        '''
        altlst, children = self._parse_object(copy.copy(obj.children), ANTLRv4Parser.LexerAltListContext)
        assert not children
        res = self.parse_lexerAltList(altlst)
        return res

    def parse_lexerAltList(self, obj):
        '''
        lexerAltList
           : lexerAlt (OR lexerAlt)*
           ;
        '''
        # a define with multiple rules
        def pred_inside(children):
            _o, children = self._parse_question_token(children, self.lexer.OR)
            if _o is None: return None
            _o, children = self._parse_object(children, ANTLRv4Parser.LexerAltContext)
            assert _o is not None
            return _o, children

        children = copy.copy(obj.children)
        o = children.pop(0)
        lalt_children = [o]

        cs, children = self._parse_star_x(children, pred_inside)
        lalt_children.extend(cs)
        res = []
        for c in lalt_children:
            o = self.parse_lexerAlt(c)
            res.append(o)
        return res

    def parse_lexerAlt(self, obj):
        '''
        lexerAlt
           : lexerElements lexerCommands?
           |
           // explicitly allow empty alts
           ;
        '''
        cs = copy.copy(obj.children)
        if not cs: return []
        _o, children = self._parse_object(cs, ANTLRv4Parser.LexerElementsContext)
        v = self.parse_lexerElements(_o)
        _o, children = self._parse_question_object(cs, ANTLRv4Parser.LexerCommandsContext)
        if _o:
            self.parse_lexerCommands(_o[0])
        return v

    def parse_lexerCommands(self, obj):
        '''
        lexerCommands
           : RARROW lexerCommand (COMMA lexerCommand)*
           ;
        '''
        # a single production rule
        def pred_inside(children):
            _o, children = self._parse_question_token(children, self.lexer.COMMA)
            if _o is None: return None
            self.parse_COMMA(_o[0])
            _o, children = self._parse_object(children, ANTLRv4Parser.LexerCommandContext)
            assert _o is not None
            return _o

        children = copy.copy(obj.children)
        _o, children = self._parse_token(children, self.lexer.RARROW)
        self.parse_RARROW(_o)
        _o, children = self._parse_object(children, ANTLRv4Parser.LexerCommandContext)
        lcommands = [_o]

        res, children = self._parse_star_x(children, pred_inside)
        lcommands.extend(res)

        res = []
        for c in lcommands:
            v = self.parse_lexerCommand(c)
            res.append(v)
        return res

    def parse_lexerCommand(self, obj):
        '''
        lexerCommand
           : lexerCommandName LPAREN lexerCommandExpr RPAREN
           | lexerCommandName
           ;
        '''
        children = copy.copy(obj.children)
        cn, children = self._parse_object(children, ANTLRv4Parser.LexerCommandNameContext)
        cname = self.parse_lexerCommandName(cn)
        if not children:
            return cname

        assert False
        _o, children = self._parse_token(children, self.lexer.LPAREN)
        self.parse_LPAREN(_o)
        ce, children = self._parse_object(children, ANTLRv4Parser.LexerCommandExprContext)
        _o, children = self._parse_token(children, self.lexer.RPAREN)
        self.parse_RPAREN(_o)
        assert not children

        cname = self.parse_lexerCommandName(cn)
        cexp = self.parse_lexerCommandExpr(ce)
        return (cname, cexp)

    def parse_lexerCommandName(self, obj):
        '''
        lexerCommandName
           : identifier
           | MODE
           ;
        '''
        children = copy.copy(obj.children)
        c = children[0]
        if isinstance(c, ANTLRv4Parser.IdentifierContext):
            _o, children = self._parse_object(children, ANTLRv4Parser.IdentifierContext)
            assert not children
            return self.parse_identifier(_o)
        elif isinstance(c, tree.Tree.TerminalNodeImpl):
            _o, children = self._parse_token(children, self.lexer.MODE)
            assert not children
            return self.parse_MODE(_o)
        else:
            assert False


    def parse_lexerCommandExpr(self, obj):
        '''
        lexerCommandExpr
           : identifier
           | INT
           ;
           // --------------------
           // Rule Alts
        '''
        raise NotImplemented()

    def parse_lexerElements(self, obj):
        '''
        lexerElements
           : lexerElement+
           ;
        '''
        _o, children = self._parse_star_object(copy.copy(obj.children), ANTLRv4Parser.LexerElementContext)
        assert len(_o) > 0 # plus
        res = []
        for val in _o:
            o = self.parse_lexerElement(val)
            res.append(o)
        return res

    def parse_lexerElement(self, obj):
        '''
        lexerElement
           : labeledLexerElement ebnfSuffix?
           | lexerAtom ebnfSuffix?
           | lexerBlock ebnfSuffix?
           | actionBlock QUESTION?
           ;
        '''
        children = copy.copy(obj.children)
        c = children.pop(0)
        if isinstance(c, ANTLRv4Parser.LabeledLexerElementContext):
            assert not children
            return self.parse_labeledLexerElement(c)
        elif isinstance(c, ANTLRv4Parser.LexerAtomContext):
            ebnf_suffix, children = self._parse_question_object(children, ANTLRv4Parser.EbnfSuffixContext)
            assert not children
            ebnfs = [self.parse_ebnfSuffix(e) for e in ebnf_suffix]
            res = self.parse_lexerAtom(c)
            if ebnfs:
                e = ebnfs.pop(0)
                assert e in {'*', '?', '+'}
                return (e, res)
            else:
                return res
        elif isinstance(c, ANTLRv4Parser.ActionBlockContext):
            assert not children
            return self.parse_actionBlock(c)
        elif isinstance(c, ANTLRv4Parser.LexerBlockContext):
            ebnf_suffix, children = self._parse_question_object(children, ANTLRv4Parser.EbnfSuffixContext)
            assert not children
            res = self.parse_lexerBlock(c)
            ebnf = None if not ebnf_suffix else [self.parse_ebnfSuffix(ebnf_suffix[0])]
            return (res, ebnf)
        else: assert False

    def parse_lexerBlock(self, obj):
        '''
        lexerBlock
           : LPAREN lexerAltList RPAREN
           ;
        '''
        children = copy.copy(obj.children)
        lparen, children = self._parse_token(children, self.lexer.LPAREN)
        self.parse_LPAREN(lparen)
        lalts, children = self._parse_object(children, ANTLRv4Parser.LexerAltListContext)
        res = self.parse_lexerAltList(lalts)
        rparen, children = self._parse_token(children, self.lexer.RPAREN)
        self.parse_RPAREN(rparen)
        assert not children
        return res

    def parse_lexerAtom(self, obj):
        '''
        lexerAtom
           : characterRange
           | terminal
           | notSet
           | LEXER_CHAR_SET
           | DOT elementOptions?
           ;
        '''
        children = copy.copy(obj.children)
        c = children.pop(0)
        assert not children
        if isinstance(c, ANTLRv4Parser.CharacterRangeContext):
            return self.parse_characterRange(c)
        elif isinstance(c, ANTLRv4Parser.TerminalContext):
            return self.parse_terminal(c)
        elif isinstance(c, ANTLRv4Parser.NotSetContext):
            return self.parse_notSet(c)
        elif isinstance(c, tree.Tree.TerminalNodeImpl):
            if c.symbol.type == self.lexer.LEXER_CHAR_SET:
                return self.parse_LEXER_CHAR_SET(c)
            elif c.symbol.type == self.lexer.DOT:
                assert False
        else:
            assert False

    def parse_rules(self, rules):
        '''
        rules
           : ruleSpec*
           ;
        '''
        ruleSpec_star, children = self._parse_star_object(copy.copy(rules.children), ANTLRv4Parser.RuleSpecContext)
        rules_json = self.parse_rulesSpec_star(ruleSpec_star)
        return rules_json

def main():
    with open(sys.argv[1], 'r') as f:
        code = f.read()
    ag = AntlrG(code)
    for elt in ag.res:
        key = elt[0]
        defs = elt[1]
        print(key)
        for rule in defs:
            print('  ', rule)

    # now print ebnf blocks
    #for k in EBNF:
    #    print(k)
    #    e, rep = EBNF[k]
    #    if rep == '*':
    #        e.append(k)
    #        print('  ', e)
    #        print('  ', [])
    #    elif rep == '+':
    #        print('  ', e)
    #    elif rep == '?':
    #        print('  ', e)
    #    else:
    #        assert False

if __name__ == '__main__':
    main()
