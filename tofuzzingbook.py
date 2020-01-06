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

    def parse_token(self, children, typ):
        assert isinstance(children[0], tree.Tree.TerminalNodeImpl)
        tok = children.pop(0)
        assert tok.symbol.type == typ
        return tok, children

    def parse_object(self, children, typ):
        assert isinstance(children[0], typ)
        obj = children.pop(0)
        return obj, children

    def parse_objectList(self, children, typ, n=-1):
        lst = []
        while children:
            if n == 0: break
            n -= 1
            if isinstance(children[0], typ):
                obj = children.pop(0)
                assert isinstance(obj, typ)
                lst.append(obj)
            else:
                break
        return lst, children

    def parse_tokenList(self, children, typ, n=-1):
        lst = []
        while children:
            if n == 0: break
            n -= 1
            if isinstance(children[0], tree.Tree.TerminalNodeImpl):
                if children[0].symbol.type != typ: break
                tok = children.pop(0)
                assert tok.symbol.type == typ
                lst.append(tok)
            else:
                break
        return lst, children

    def parse_grammarSpec(self, parsedtree):
        '''
        grammarSpec
           : DOC_COMMENT* grammarDecl prequelConstruct* rules modeSpec* EOF
           ;
        '''
        children = copy.copy(parsedtree.children)
        # if there are doc_comments, skip them first
        _o, children = self.parse_tokenList(children, self.lexer.DOC_COMMENT)
        self.parse_DOC_COMMENT_star(_o)

        _o, children = self.parse_object(children, ANTLRv4Parser.GrammarDeclContext)
        self.parse_grammarDecl(_o)

        _o, children = self.parse_objectList(children, ANTLRv4Parser.PrequelConstructContext)
        self.parse_prequelConstruct_star(_o)

        rules, children = self.parse_object(children, ANTLRv4Parser.RulesContext)
        rules_json = self.parse_rules(rules)

        _o, children = self.parse_objectList(children, ANTLRv4Parser.ModeSpecContext)
        self.parse_modeSpec_star(_o)

        _o, children = self.parse_token(children, self.parser.EOF)
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
        children = copy.copy(rspec.children)
        # parse and ignore
        _o, children = self.parse_tokenList(children, self.lexer.DOC_COMMENT)
        self.parse_DOC_COMMENT_star(_o)

        _o, children = self.parse_objectList(children, ANTLRv4Parser.RuleModifiersContext, n=1) # a maximum of one
        self.parse_ruleModifiers_question(_o)

        _o, children = self.parse_token(children, self.lexer.RULE_REF)
        rule_name = self.parse_RULE_REF(_o)

        return [rule_name, []]

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
        _o, children = self.parse_tokenList(children, self.lexer.DOC_COMMENT)
        self.parse_DOC_COMMENT_star(_o)

        _o, children = self.parse_tokenList(children, self.lexer.FRAGMENT, n=1)
        self.parse_FRAGMENT_question(_o)

        _o, children = self.parse_token(children, self.lexer.TOKEN_REF)
        token_name = self.parse_TOKEN_REF(_o)

        _o, children = self.parse_token(children, self.lexer.COLON)

        _o, children = self.parse_object(children, ANTLRv4Parser.LexerRuleBlockContext)

        _o, children = self.parse_token(children, self.lexer.SEMI)

        return [token_name, []]

    def parse_rules(self, rules):
        '''
        rules
           : ruleSpec*
           ;
        '''
        ruleSpec_star, children = self.parse_objectList(copy.copy(rules.children), ANTLRv4Parser.RuleSpecContext)
        rules_json = self.parse_rulesSpec_star(ruleSpec_star)
        return rules_json

def main():
    with open(sys.argv[1], 'r') as f:
        code = f.read()
    ag = AntlrG(code)
    print(ag.res)

if __name__ == '__main__':
    main()
