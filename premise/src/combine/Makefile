all: combf
combf: utils.ml format.ml algs.ml combf.ml
	ocamlopt -inline 100 -unsafe unix.cmxa str.cmxa $^ -o $@
	rm *[.]cm* *[.]o

clean:
	rm combf

