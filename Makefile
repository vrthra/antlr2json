export PYTHONPATH=build
python=./bin/p

target=JSON

all: build/$(target).fbjson

show: build/$(target).fbjson
	$(python) src/show.py build/$(target).fbjson

fuzz: build/$(target).fbjson
	$(python) src/fuzz.py build/$(target).fbjson

build/$(target).fbjson: build/$(target).ebnf
	$(python) src/ebnftosimple.py build/$(target).ebnf > build/$(target).fbjson_
	cat build/$(target).fbjson_ | jq . > build/$(target).fbjson
	rm -f build/$(target).fbjson_

build/$(target).ebnf: examples/$(target).g4 build/ANTLRv4Lexer.py build/ANTLRv4Parser.py | build
	$(python) src/tojson.py examples/$(target).g4 > build/$(target).ebnf_
	cat build/$(target).ebnf_ | jq . > build/$(target).ebnf
	rm -f build/$(target).ebnf_

build/JavaScript.fbjson: build/JavaScriptLexer.ebnf  build/JavaScriptParser.ebnf
	$(python) src/ebnftosimple.py build/JavaScriptLexer.ebnf build/JavaScriptParser.ebnf > build/JavaScript.fbjson_
	cat build/JavaScript.fbjson_ | jq . > build/JavaScript.fbjson
	rm -f build/JavaScript.fbjson_

build/%.ebnf: examples/%.g4 build/ANTLRv4Lexer.py build/ANTLRv4Parser.py | build
	$(python) src/tojson.py examples/$*.g4 > build/$*.ebnf_
	cat build/$*.ebnf_ | jq . > build/$*.ebnf
	rm -f build/$*.ebnf_

build/ANTLRv4Lexer.py: src/ANTLRv4Lexer.g4 | build
	java -Xmx500M -cp ../antlr-4.7.2-complete.jar org.antlr.v4.Tool -Xexact-output-dir -o build -Dlanguage=Python3 src/ANTLRv4Lexer.g4

build/ANTLRv4Parser.py: src/ANTLRv4Parser.g4 | build
	java -Xmx500M -cp ../antlr-4.7.2-complete.jar org.antlr.v4.Tool -Xexact-output-dir -o build -lib build -Dlanguage=Python3 src/ANTLRv4Parser.g4

prereq:
	wget https://www.antlr.org/download/antlr-4.7.2-complete.jar
	mv antlr-4.7.2-complete.jar ..
	pip install wheel
	pip install antlr4-python3-runtime==4.7.2

build/%Parser.py: examples/%.g4
	java -Xmx500M -cp ../antlr-4.7.2-complete.jar org.antlr.v4.Tool -Xexact-output-dir -o build -Dlanguage=Python3 examples/$*.g4

build/%Lexer.py: examples/%.g4
	java -Xmx500M -cp ../antlr-4.7.2-complete.jar org.antlr.v4.Tool -Xexact-output-dir -o build -Dlanguage=Python3 examples/$*.g4

inp=examples/rhino.385.js

parse: build/JavaScript.fbjson
	./bin/p src/fbparse.py build/JavaScript.fbjson $(inp)

build:;mkdir -p build

debug:
	./bin/pudb tojson.py examples/$(target).g4

clean:
	rm -rf build; mkdir -p build
