import codecs
from antlr4 import *
from ANTLRv4Lexer import ANTLRv4Lexer as MyLexer
from ANTLRv4Parser import ANTLRv4Parser as MyParser
import sys
import copy

def warn(v):
    pass

class AntlrG:
    def __init__(self, code):
        self.lexer = MyLexer(InputStream(code))

        tokenStream = CommonTokenStream(self.lexer)
        self.parser = MyParser(tokenStream)
        self.parser.buildParseTrees = True

        self.tree = self.parser.grammarSpec() # entry
        self.gtype, self.gid, self.res = self.parse_grammarSpec(self.tree)

    def toStr(self, tree):
        return tree.toStringTree(recog=self.parser)

    def toJSON(self):
        v = {elt[0]: elt[1] for elt in self.res}
        return {'[start]':self.res[0][0], '[grammar]':v}

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

        _o, children = self._parse_object(children, self.parser.GrammarDeclContext)
        typename, gid = self.parse_grammarDecl(_o)

        _o, children = self._parse_star_object(children, self.parser.PrequelConstructContext)
        self.parse_prequelConstruct_star(_o)

        rules, children = self._parse_object(children, self.parser.RulesContext)
        rules_json = self.parse_rules(rules)

        _o, children = self._parse_star_object(children, self.parser.ModeSpecContext)
        self.parse_modeSpec_star(_o)

        _o, children = self._parse_token(children, self.parser.EOF)
        self.parse_EOF(_o)
        return (typename, gid, rules_json)

    def parse_DOT(self, obj):
        return ('dot', obj.symbol.text)

    def parse_LEXER_CHAR_SET(self, obj):
        return ('charset', obj.symbol.text)

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

    def parse_modeSpec_star(self, children):
        # no support for modes now.
        assert not children
        return None

    def parse_grammarType(self, obj):
        '''
        grammarType
           : (LEXER GRAMMAR | PARSER GRAMMAR | GRAMMAR)
          ;
        '''
        children = copy.copy(obj.children)
        kind = 'Both'
        if len(children) == 2:
            c = children.pop(0)
            if isinstance(c, tree.Tree.TerminalNodeImpl):
                if c.symbol.type == self.lexer.LEXER:
                    kind = 'Lexer'
                elif c.symbol.type == self.lexer.PARSER:
                    kind = 'Parser'
                else:
                    assert False
        _o, children = self._parse_token(children, self.lexer.GRAMMAR)
        assert not children
        return kind

    def parse_grammarDecl(self, obj):
        # SKIPPED
        '''
        grammarDecl
           : grammarType identifier SEMI
           ;
        '''
        children = copy.copy(obj.children)
        _o, children = self._parse_object(children, self.parser.GrammarTypeContext)
        gtype = self.parse_grammarType(_o)
        _o, children = self._parse_object(children, self.parser.IdentifierContext)
        idname = self.parse_identifier(_o)
        _o, children = self._parse_token(children, self.lexer.SEMI)
        assert _o
        assert not children
        return (gtype, idname)

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
        if isinstance(rspec, self.parser.ParserRuleSpecContext):
            return self.parse_parserRuleSpec(rspec)
        elif isinstance(rspec, self.parser.LexerRuleSpecContext):
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

        _o, children = self._parse_question_object(children, self.parser.RuleModifiersContext) # a maximum of one
        self.parse_ruleModifiers_question(_o)

        _o, children = self._parse_token(children, self.lexer.RULE_REF)
        rule_name = self.parse_RULE_REF(_o)

        _o, children = self._parse_question_object(children, self.parser.ArgActionBlockContext)
        _o, children = self._parse_question_object(children, self.parser.RuleReturnsContext)
        _o, children = self._parse_question_object(children, self.parser.ThrowsSpecContext)
        _o, children = self._parse_question_object(children, self.parser.LocalsSpecContext)
        _o, children = self._parse_star_object(children, self.parser.RulePrequelContext)

        _o, children = self._parse_token(children, self.lexer.COLON)
        _o, children = self._parse_object(children, self.parser.RuleBlockContext)
        defines = self.parse_ruleBlock(_o)

        _o, children = self._parse_token(children, self.lexer.SEMI)
        _o, children = self._parse_object(children, self.parser.ExceptionGroupContext)

        return [rule_name, defines]


    def parse_ruleBlock(self, rb):
        '''
        ruleBlock
           : ruleAltList
           ;
        '''
        # a define with multiple rules
        _o, children = self._parse_object(copy.copy(rb.children), self.parser.RuleAltListContext)
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
            if not _o: return None, children
            _o, children = self._parse_question_object(children, self.parser.LabeledAltContext)
            if not _o: return None, children
            return _o[0], children

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
        def pred_inside(children):
            _o, children = self._parse_question_token(children, self.lexer.POUND)
            if not _o: return None, children
            _o, children = self._parse_question_object(children, self.parser.IdentifierContext)
            if not _o: return None, children
            return _o[0], children

        children = obj.children
        ac, children = self._parse_object(children, self.parser.AlternativeContext)
        acr =  self.parse_alternative(ac)
        assert acr[0] == 'seq'
        res, children = self._parse_question_x(children, pred_inside)
        assert not children

        return acr

    def parse_elementOptions(self, obj):
        '''
        elementOptions
           : LT elementOption (COMMA elementOption)* GT
           ;
        '''
        children = copy.copy(obj.children)
        _o, children = self._parse_token(children, self.lexer.LT)


        # a single production rule
        def pred_inside(children):
            _o, children = self._parse_question_token(children, self.lexer.COMMA)
            if not _o: return None, children
            _o, children = self._parse_question_object(children, self.parser.ElementOptionContext)
            if not _o: return None, children
            return _o[0], children

        eo, children = self._parse_object(children, self.parser.ElementOptionContext)
        res, children = self._parse_star_x(children, pred_inside)
        lst = [eo] + res
        _o, children = self._parse_token(children, self.lexer.GT)
        return lst


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
            return ('seq', [])
        _o, children = self._parse_question_object(children, self.parser.ElementOptionsContext)
        eo = None
        if _o:
            eo = self.parse_elementOptions(_o[0])
        elts, children = self._parse_star_object(children, self.parser.ElementContext)
        assert len(elts) >= 1 # element+
        res = []
        for e in elts:
            r = self.parse_element(e)
            res.append(r)
        return ('seq', res)

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
        if isinstance(c, self.parser.LabeledElementContext):
            """
            dropDatabase
               : DROP dbFormat=(DATABASE | SCHEMA) ifExists? uid
               ;
            """
            le = self.parse_labeledElement(c)
            ebnf = None
            if len(children) > 1:
                ebnf = self.parse_ebnfSuffix(children[1])
                return (ebnf, le)
            return le
        elif isinstance(c, self.parser.AtomContext):
            le = self.parse_atom(c)
            ebnf = None
            if len(children) > 1:
                ebnf = self.parse_ebnfSuffix(children[1])
                return (ebnf, le)
            return le
        elif isinstance(c, self.parser.EbnfContext):
            blksuffix, blk = self.parse_ebnf(c)
            if blksuffix is None:
                return blk
            else:
                return (blksuffix, blk)

        elif isinstance(c, self.parser.ActionBlockContext):
            #warn('ActionBlock found at: %d' % c.start.line)
            ab = self.parse_actionBlock(c)
            return ('action', ab)
        else:
            assert False

    def parse_actionBlock(self, obj):
        '''
        actionBlock
           : BEGIN_ACTION ACTION_CONTENT* END_ACTION
          ;
        '''
        children = copy.copy(obj.children)
        b, children = self._parse_token(children, self.lexer.BEGIN_ACTION)
        cs, children = self._parse_star_token(children, self.lexer.ACTION_CONTENT)
        e, children = self._parse_token(children, self.lexer.END_ACTION)
        return '%s %s %s' % (b.symbol.text, ''.join([c.symbol.text for c in cs]), e.symbol.text)

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

        elif isinstance(c, self.parser.CharacterRangeContext):
            assert not children
            return self.parse_characterRange(c)
        else:
            assert False

    def parse_characterRange(self, obj):
        '''
        characterRange
           : STRING_LITERAL RANGE STRING_LITERAL
           ;
        '''
        children = copy.copy(obj.children)
        _o, children = self._parse_token(children, self.lexer.STRING_LITERAL)
        a = self.parse_STRING_LITERAL(_o)
        _o, children = self._parse_token(children, self.lexer.RANGE)
        _o, children = self._parse_token(children, self.lexer.STRING_LITERAL)
        b = self.parse_STRING_LITERAL(_o)
        return ('charrange', a, b)

    def parse_ebnf(self, obj):
        '''
        ebnf
           : block blockSuffix?
           ;
        '''
        children = copy.copy(obj.children)
        _o, children = self._parse_object(children, self.parser.BlockContext)
        v = self.parse_block(_o)

        _o, children = self._parse_question_object(children, self.parser.BlockSuffixContext)
        if _o:
            v1 = self.parse_blockSuffix(_o[0])
            # v1 could be *, +, ?, *?, +?, or ??
            return (v1, v)
        return (None, v)

    def parse_blockSuffix(self, obj):
        '''
        blockSuffix
           : ebnfSuffix
           ;
        '''
        children = obj.children
        _o, children = self._parse_object(children, self.parser.EbnfSuffixContext)
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
        # assert not children # How to handle ?? or *? or +?
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
            _o1, children = self._parse_question_object(children, self.parser.OptionsSpecContext)
            assert not _o1
            _o2, children = self._parse_star_object(children, self.parser.RuleActionContext)
            assert not _o2
            _o3, children = self._parse_question_token(children, self.lexer.COLON)
            if not _o3:
                return None, children_
            o = _o3[0]
            return o, children

        res, children = self._parse_question_x(children, pred_inside)
        #assert not res # this is a question. res can be empty
        altlst, children = self._parse_object(children, self.parser.AltListContext)
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
        alt, children = self._parse_object(children, self.parser.AlternativeContext)

        # a single production rule
        def pred_inside(children):
            _o, children = self._parse_question_token(children, self.lexer.OR)
            if not _o: return None, children
            _o, children = self._parse_question_object(children, self.parser.AlternativeContext)
            if not _o: return None, children
            return _o[0], children

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
        if isinstance(c, self.parser.TerminalContext):
            # note: this may simply be a parser terminal. It does
            # not mean that it is a lexer terminal
            return self.parse_terminal(c)
        elif isinstance(c, self.parser.RulerefContext):
            return self.parse_ruleref(c)
        elif isinstance(c, self.parser.NotSetContext):
            return self.parse_notSet(c)
        else:
            assert isinstance(c, tree.Tree.TerminalNodeImpl)
            if c.symbol.type == self.lexer.LEXER_CHAR_SET:
                return self.parse_LEXER_CHAR_SET(c)
            elif c.symbol.type == self.lexer.DOT:
                return self.parse_DOT(c)
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
        if isinstance(c, self.parser.SetElementContext):
            v = self.parse_setElement(c)
            return ('not', v)
        elif isinstance(c, self.parser.BlockSetContext):
            v = self.parse_blockSet(c)
            return ('not', v)
        else: assert False

    def parse_blockSet(self, obj):
        '''
        blockSet
            : LPAREN setElement (OR setElement)* RPAREN
            ;
        '''
        children = copy.copy(obj.children)
        _o, children = self._parse_token(children, self.lexer.LPAREN)
        _o, children = self._parse_object(children, self.parser.SetElementContext)

        assert _o is not None
        selt_children = [_o]

        # a define with multiple rules
        def pred_inside(children):
            _o, children = self._parse_question_token(children, self.lexer.OR)
            if not _o: return None, children
            _o, children = self._parse_question_object(children, self.parser.SetElementContext)
            if not _o: return None, children
            return _o[0], children
        cs, children = self._parse_star_x(children, pred_inside)
        selt_children.extend(cs)

        res = []
        for c in selt_children:
            o = self.parse_setElement(c)
            res.append(o)
        return ('seq', res)


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
            _o, children = self._parse_question_object(children, self.parser.ElementOptionsContext)
            assert not _o
            return v
        elif c.symbol.type == self.lexer.STRING_LITERAL:
            v = self.parse_STRING_LITERAL(c)
            _o, children = self._parse_question_object(children, self.parser.ElementOptionsContext)
            assert not _o
            return v
        else:
            assert False

    def parse_STRING_LITERAL(self, obj):
        v = obj.symbol.text
        assert (v[0], v[-1]) == ("'","'")
        # we have removed '. So if there was an escape involved (\') then
        # we should unescape it too.
        # we can not use ast.literal_eval here as the ALTLR4 format
        # uses \uXXXX format to specify the unicode characters, which
        # gets converted to the actual unicode chars during literal_eval.
        return v[1:-1].replace("\\'", "'")

    def parse_ruleref(self, obj):
        '''
        ruleref
           : RULE_REF argActionBlock? elementOptions?
           ;
        '''
        children = obj.children
        _o, children = self._parse_token(children, self.lexer.RULE_REF)
        v = self.parse_RULE_REF(_o)
        _o, children = self._parse_question_object(children, self.parser.ArgActionBlockContext)
        assert not _o
        _o, children = self._parse_question_object(children, self.parser.ElementOptionsContext)
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
        _o, children = self._parse_object(children, self.parser.IdentifierContext)
        o = self.parse_identifier(_o)
        assign = children.pop(0)
        assert isinstance(assign, tree.Tree.TerminalNodeImpl)
        nxt = children.pop(0)
        res = None
        if isinstance(nxt, self.parser.AtomContext):
            res = self.parse_atom(nxt)
        elif isinstance(nxt, self.parser.BlockContext):
            """(DATABASE | SCHEMA)"""
            #assert False
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

        _o, children = self._parse_object(children, self.parser.LexerRuleBlockContext)
        tdef = self.parse_lexerRuleBlock(_o)

        _o, children = self._parse_token(children, self.lexer.SEMI)

        return [token_name, tdef]

    def parse_lexerRuleBlock(self, obj):
        '''
        lexerRuleBlock
           : lexerAltList
           ;
        '''
        altlst, children = self._parse_object(copy.copy(obj.children), self.parser.LexerAltListContext)
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
            if not _o: return None, children
            _o, children = self._parse_question_object(children, self.parser.LexerAltContext)
            if not _o: return None, children
            return _o[0], children

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
        _o, children = self._parse_object(cs, self.parser.LexerElementsContext)
        v = self.parse_lexerElements(_o)
        _o, children = self._parse_question_object(cs, self.parser.LexerCommandsContext)
        if _o:
            cmd = self.parse_lexerCommands(_o[0])
            return ('action', cmd, ('seq', v))
        return ('seq', v)

    def parse_lexerCommands(self, obj):
        '''
        lexerCommands
           : RARROW lexerCommand (COMMA lexerCommand)*
           ;
        '''
        # a single production rule
        def pred_inside(children):
            _o, children = self._parse_question_token(children, self.lexer.COMMA)
            if not _o: return None, children
            self.parse_COMMA(_o[0])
            _o, children = self._parse_question_object(children, self.parser.LexerCommandContext)
            if not _o: return None, children
            return _o[0], children

        children = copy.copy(obj.children)
        _o, children = self._parse_token(children, self.lexer.RARROW)
        self.parse_RARROW(_o)
        _o, children = self._parse_object(children, self.parser.LexerCommandContext)
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
        cn, children = self._parse_object(children, self.parser.LexerCommandNameContext)
        cname = self.parse_lexerCommandName(cn)
        if not children:
            return cname

        _o, children = self._parse_token(children, self.lexer.LPAREN)
        self.parse_LPAREN(_o)
        ce, children = self._parse_object(children, self.parser.LexerCommandExprContext)
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
        if isinstance(c, self.parser.IdentifierContext):
            _o, children = self._parse_object(children, self.parser.IdentifierContext)
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
        children = copy.copy(obj.children)
        c = children[0]
        if isinstance(c, self.parser.IdentifierContext):
            _o, children = self._parse_object(copy.copy(obj.children), self.parser.IdentifierContext)
            assert not children
            return self.parse_identifier(_o)
        elif isinstance(c, tree.Tree.TerminalNodeImpl):
            _o, children = self._parse_token(children, self.lexer.MODE)
            assert not children
            return self.parse_INT(_o)
        else:
            assert False

    def parse_lexerElements(self, obj):
        '''
        lexerElements
           : lexerElement+
           ;
        '''
        _o, children = self._parse_star_object(copy.copy(obj.children), self.parser.LexerElementContext)
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
        if isinstance(c, self.parser.LabeledLexerElementContext):
            assert not children
            return self.parse_labeledLexerElement(c)
        elif isinstance(c, self.parser.LexerAtomContext):
            ebnf_suffix, children = self._parse_question_object(children, self.parser.EbnfSuffixContext)
            assert not children
            ebnfs = [self.parse_ebnfSuffix(e) for e in ebnf_suffix]
            res = self.parse_lexerAtom(c)
            if ebnfs:
                e = ebnfs.pop(0)
                # assert e in {'*', '?', '+'}
                return (e, res)
            else:
                return res
        elif isinstance(c, self.parser.ActionBlockContext):
            res = self.parse_actionBlock(c)
            q, children = self._parse_question_token(children, self.lexer.QUESTION)
            assert not children
            if not q:
                return ('action', res)
            else:
                r = q[0]
                qv = self.parse_QUESTION(r)
                return ('action', (qv, res))

        elif isinstance(c, self.parser.LexerBlockContext):
            ebnf_suffix, children = self._parse_question_object(children, self.parser.EbnfSuffixContext)
            assert not children
            res = self.parse_lexerBlock(c)
            ebnfs = [self.parse_ebnfSuffix(e) for e in ebnf_suffix]
            if ebnfs:
                e = ebnfs.pop(0)
                assert e in {'*', '?', '+'}
                return (e, res)
            else:
                return res
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
        lalts, children = self._parse_object(children, self.parser.LexerAltListContext)
        res = self.parse_lexerAltList(lalts)
        rparen, children = self._parse_token(children, self.lexer.RPAREN)
        self.parse_RPAREN(rparen)
        assert not children
        return ('or', res)

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
        if isinstance(c, self.parser.CharacterRangeContext):
            return self.parse_characterRange(c)
        elif isinstance(c, self.parser.TerminalContext):
            return self.parse_terminal(c)
        elif isinstance(c, self.parser.NotSetContext):
            return self.parse_notSet(c)
        elif isinstance(c, tree.Tree.TerminalNodeImpl):
            if c.symbol.type == self.lexer.LEXER_CHAR_SET:
                return self.parse_LEXER_CHAR_SET(c)
            elif c.symbol.type == self.lexer.DOT:
                return self.parse_DOT(c)
        else:
            assert False

    def parse_rules(self, rules):
        '''
        rules
           : ruleSpec*
           ;
        '''
        ruleSpec_star, children = self._parse_star_object(copy.copy(rules.children), self.parser.RuleSpecContext)
        rules_json = self.parse_rulesSpec_star(ruleSpec_star)
        return rules_json

import json
def main():
    with open(sys.argv[1], 'r') as f:
        code = f.read()
        # code = codecs.escape_decode(bytes(mystring, "utf-8"))[0].decode("utf-8")
        # code = bytes(mystring, 'utf-8').decode('unicode_escape')
    ag = AntlrG(code)
    res = ag.toJSON()
    res['[kind]'] = ag.gtype
    res['[gname]'] = ag.gid
    res['[tree]'] = ag.toStr(ag.tree)
    print(json.dumps(res))
if __name__ == '__main__':
    main()
