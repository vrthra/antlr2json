from antlr4 import *
from ANTLRv4Lexer import ANTLRv4Lexer
from ANTLRv4Parser import ANTLRv4Parser
import sys
import copy


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


    def parse_EOF(self, children): return None

    def parse_prequelConstruct_star(self, children): return None

    def parse_prequelConstruct(self, children):
        '''
        prequelConstruct
           : optionsSpec
           | delegateGrammars
           | tokensSpec
           | channelsSpec
           | action_
           ;
        '''
        ...

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
        _o, children = self._parse_object(copy.copy(rb.children), ANTLRv4Parser.RuleAltListContext)
        assert not children
        return self.parse_ruleAltList(_o)

    def parse_ruleAltList(self, ral):
        '''
        ruleAltList
           : labeledAlt (OR labeledAlt)*
           ;
        '''
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
        children = copy.copy(obj.children)
        c = children[0]
        if isinstance(c, ANTLRv4Parser.LabeledElementContext):
            le = self.parse_labeledElement(c)
            ebnf = None
            if len(children) > 1:
                ebnf = self.parse_ebnfSuffix(children[1])
                return [le, ebnf]
            return [le]
        elif isinstance(c, ANTLRv4Parser.AtomContext):
            le = self.parse_atom(c)
            ebnf = None
            if len(children) > 1:
                ebnf = self.parse_ebnfSuffix(children[1])
                return [le, ebnf]
            return [le]
        elif isinstance(c, ANTLRv4Parser.EbnfContext):
            return self.parse_ebnf(c)
        elif isinstance(c, ANTLRv4Parser.ActionBlockContext):
            raise NotImplemented()
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
            return [v, v1]
        return [v]

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
        assert isinstance(c, tree.Tree.TerminalNodeImpl)
        if c.symbol.type == self.lexer.QUESTION:
            _o, children = self._parse_question_token(children, self.lexer.QUESTION)
            return [c.symbol.text, [i.symbol.text for i in _o]]
        elif c.symbol.type == self.lexer.STAR:
            _o, children = self._parse_question_token(children, self.lexer.QUESTION)
            return [c.symbol.text, [i.symbol.text for i in _o]]
        elif c.symbol.type == self.lexer.PLUS:
            _o, children = self._parse_question_token(children, self.lexer.QUESTION)
            return [c.symbol.text, [i.symbol.text for i in _o]]
        else:
            assert False

    def parse_block(self, obj):
        '''
        block
           : LPAREN (optionsSpec? ruleAction* COLON)? altList RPAREN
        ;
        '''
        return '<block: todo>'

    def parse_atom(self, obj):
        '''
        atom
           : terminal
           | ruleref
           | notSet
           | DOT elementOptions?
           ;
        '''
        children = obj.children
        c = children[0]
        if isinstance(c, ANTLRv4Parser.TerminalContext):
            return self.parse_terminal(c)
        elif isinstance(c, ANTLRv4Parser.RulerefContext):
            return self.parse_ruleref(c)
        elif isinstance(c, ANTLRv4Parser.NotSetContext):
            return self.parse_notSet(c)
        else:
            assert isinstance(c, tree.Tree.TerminalNodeImpl)
            raise NotImplemented()

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

    def parse_STRING_LITERAL(self, obj): return obj.symbol.text

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

    def parse_RULE_REF(self, obj): return obj.symbol.text

    def parse_TOKEN_REF(self, obj): return obj.symbol.text

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

        _o, children = self._parse_token(children, self.lexer.SEMI)

        return [token_name, []]

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
    print(ag.res)

if __name__ == '__main__':
    main()
