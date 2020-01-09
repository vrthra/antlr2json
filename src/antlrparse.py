import codecs
from antlr4 import *
from JavaScriptLexer import  JavaScriptLexer as MyLexer
from JavaScriptParser import JavaScriptParser as MyParser
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

        self.tree = self.parser.program() # entry
        self.res = self.toStr(self.tree)

    def toStr(self, tree):
        return tree.toStringTree(recog=self.parser)

import json
def main():
    with open(sys.argv[1], 'r') as f:
        code = f.read()
    ag = AntlrG(code)
    res = {}
    res['[tree]'] = ag.toStr(ag.tree)
    print(json.dumps(res))
if __name__ == '__main__':
    main()
