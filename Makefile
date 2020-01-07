

all:
	java -Xmx500M -cp ../antlr-4.7.2-complete.jar org.antlr.v4.Tool -Dlanguage=Python3 ANTLRv4Lexer.g4
	java -Xmx500M -cp ../antlr-4.7.2-complete.jar org.antlr.v4.Tool -Dlanguage=Python3 ANTLRv4Parser.g4

prereq:
	wget https://www.antlr.org/download/antlr-4.7.2-complete.jar
	mv antlr-4.7.2-complete.jar ..
	pip install wheel
	pip install antlr4-python3-runtime

run:
	python3  tofuzzingbook.py examples/JSON.g4
