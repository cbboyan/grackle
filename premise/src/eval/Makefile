all: mlstats
	rm -f *[.]cm* *[.]o

mlstats: utils.ml format.ml mlstats.ml
	ocamlopt -inline 100 -unsafe unix.cmxa str.cmxa $^ -o $@
clean:
	rm mlstats combf lsi_ref write_problems stat latex_stat *cmo *cmi *cmx *o
