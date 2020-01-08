export PYTHONPATH=build

show: build/JSON.fbjson
	python3 src/show.py build/JSON.fbjson

fuzz: build/JSON.fbjson
	python3 src/fuzz.py build/JSON.fbjson

build/JSON.fbjson: build/JSON.ebnf
	python3 src/ebnftosimple.py build/JSON.ebnf > build/JSON.fbjson

build/JSON.ebnf: examples/JSON.g4 build/ANTLRv4Lexer.py build/ANTLRv4Parser.py | build
	python3 src/tojson.py examples/JSON.g4 > build/JSON.ebnf

build/ANTLRv4Lexer.py: src/ANTLRv4Lexer.g4 | build
	java -Xmx500M -cp ../antlr-4.7.2-complete.jar org.antlr.v4.Tool -Xexact-output-dir -o build -Dlanguage=Python3 src/ANTLRv4Lexer.g4

build/ANTLRv4Parser.py: src/ANTLRv4Parser.g4 | build
	java -Xmx500M -cp ../antlr-4.7.2-complete.jar org.antlr.v4.Tool -Xexact-output-dir -o build -lib build -Dlanguage=Python3 src/ANTLRv4Parser.g4

prereq:
	wget https://www.antlr.org/download/antlr-4.7.2-complete.jar
	mv antlr-4.7.2-complete.jar ..
	pip install wheel
	pip install antlr4-python3-runtime

D=-m pudb

build:;mkdir -p build

debug:
	python3 $(D) tojson.py examples/JSON.g4

clean:
	rm -f build/ANTLRv4Lexer.py build/ANTLRv4Parser.py build/ANTLRv4Lexer.interp build/ANTLRv4Parser.interp build/ANTLRv4Lexer.tokens build/ANTLRv4Parser.tokens build/ANTLRv4ParserListener.py
	rm -rf src/__pycache__/
	rm -rf build/JSON.ebnf
	rm -rf build/JSON.fbjson
