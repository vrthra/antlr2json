JSON.fbjson: JSON.ebnf
	python3 ebnftosimple.py JSON.ebnf > JSON.fbjson
	python3 show.py JSON.fbjson

JSON.ebnf: examples/JSON.g4 ANTLRv4Lexer.py ANTLRv4Parser.py
	python3 tojson.py examples/JSON.g4 > JSON.ebnf
	python3 show.py JSON.ebnf

ANTLRv4Lexer.py: ANTLRv4Lexer.g4
	java -Xmx500M -cp ../antlr-4.7.2-complete.jar org.antlr.v4.Tool -Dlanguage=Python3 ANTLRv4Lexer.g4

ANTLRv4Parser.py: ANTLRv4Parser.g4
	java -Xmx500M -cp ../antlr-4.7.2-complete.jar org.antlr.v4.Tool -Dlanguage=Python3 ANTLRv4Parser.g4

prereq:
	wget https://www.antlr.org/download/antlr-4.7.2-complete.jar
	mv antlr-4.7.2-complete.jar ..
	pip install wheel
	pip install antlr4-python3-runtime

D=-m pudb

debug:
	python3 $(D) tojson.py examples/JSON.g4

clean:
	rm -f ANTLRv4Lexer.py ANTLRv4Parser.py ANTLRv4Lexer.interp ANTLRv4Parser.interp ANTLRv4Lexer.tokens ANTLRv4Parser.tokens ANTLRv4ParserListener.py
	rm -rf __pycache__/
	rm -rf JSON.ebnf
	rm -rf JSON.fbjson
