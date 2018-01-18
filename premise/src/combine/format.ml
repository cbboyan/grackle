open Utils;;

let split_space_no_quote =
  let rxps = Str.regexp " " in
  fun s2 ->
    let rec dol = function
        [] -> []
      | [h] -> [h]
      | h1 :: (h2 :: t as tt) ->
          if h1.[0] = '\'' then
            if h1.[String.length h1 - 1] = '\'' then h1 :: dol tt
            else dol ((h1 ^ " " ^ h2) :: t)
          else h1 :: dol tt
    in dol (Str.split rxps s2)
;;

let split_one_colon_no_quote =
  let rxps = Str.regexp ":" in
  fun s2 ->
    let rec dol = function
      | h1 :: (h2 :: t as tt) ->
          if h1.[0] = '\'' then
            if h1.[String.length h1 - 1] = '\'' then (h1, String.concat ":" tt)
            else dol ((h1 ^ ":" ^ h2) :: t)
          else (h1, String.concat ":" tt)
      | _ -> failwith "split_one_colon"
    in dol (Str.split rxps s2)
;;

let dep_file_iter fname fn =
  let it_f n l =
    let (s1, s2) = split_one_colon_no_quote l in
    fn n s1 (split_space_no_quote s2)
  in file_iter fname it_f;;

let read_order fname exp =
  let h = Hashtbl.create exp in
  let it_f n s = if Hashtbl.mem h s then failwith "read_seq: dup" else Hashtbl.add h s n in
  file_iter fname it_f;
  let a = Array.create (Hashtbl.length h) "" in
  Hashtbl.iter (fun s n -> a.(n) <- s) h;
  (Hashtbl.find h, Array.get a, Array.length a);;

let read_deps fname th_num th_no =
  let deps = Array.create th_num [] in
  let it_f n h d =
    let th_no s = try th_no s with Not_found -> failwith ("read_deps: notfound:" ^ s) in
    let hh = th_no h in
    let dd = List.rev (List.fold_left (fun sf d -> try th_no d :: sf with _ -> sf) [] d) in
    (*let df = List.filter (fun i -> i < hh) dd in*)
    (*if df <> dd then Printf.eprintf "Warning: future dependencies used\n%!";*)
    deps.(hh) <- dd
  in
  dep_file_iter fname it_f; Array.get deps
;;

let rxpsyms = Str.regexp "\", \"";;
let read_sym_line l =
  let (s1,s2) = split_one_colon_no_quote l in
  let s2 = String.sub s2 1 (String.length s2 - 2) in
  s1, Str.split rxpsyms s2
;;

let read_syms fname th_num th_no exp =
  let inc = open_in fname
  and th_syms = Array.create th_num []
  and sym_no = Hashtbl.create 100000
  and prevsym = ref (-1) in
  let find_sym s =
    try Hashtbl.find sym_no s
    with Not_found -> incr prevsym; Hashtbl.add sym_no s !prevsym; !prevsym
  in
  (try while true do
    let (h, d) = read_sym_line (input_line inc) in
    let syms = setify (List.map find_sym d) in
let tn = try th_no h with Not_found -> failwith ("read_syms:not_found" ^ h) in
    if th_syms.(tn) <> [] then failwith ("read_syms: dup: " ^ h);
    th_syms.(tn) <- syms
  done with End_of_file -> close_in inc);
  let sym_num = 1 + !prevsym in
  let sym_ths = Array.create sym_num [] in
  Array.iteri (fun th syms -> List.iter (fun s -> sym_ths.(s) <- th :: sym_ths.(s)) syms) th_syms;
  (Array.get th_syms, Array.get sym_ths, sym_num)
;;

let read_statements fname th_num th_no =
  let h = Hashtbl.create th_num in
  let read_all _ s =
    let l = String.length s in
    if l < 4 then failwith ("read_all: too short: " ^ s);
    if String.sub s 0 4 <> "fof(" then failwith ("read_all: no fof: " ^ s);
    if String.sub s (l - 2) 2 <> ")." then failwith ("read_all: no end parenthesis: " ^ s);
    let co1 = try String.index s ',' with Not_found -> failwith "read_all: no comma" in
    let co2 = try String.index_from s (co1 + 1) ',' with Not_found -> failwith "read_all: no comma2" in
    let nm = String.sub s 4 (co1 - 4) and s = String.sub s (co2 + 1) (l - co2 - 3) in
    let n = try th_no nm with _ -> failwith ("read_all: th_no failed: " ^ nm) in
    Hashtbl.replace h n s
  in
  file_iter fname read_all;
  Hashtbl.find h;;

let read_snow fname th_num =
  let rxp = Str.regexp "[][,() ]+" in
  let a = Array.create th_num [] in
  let read n s =
    let rec read_vals acc = function
        [] -> acc
      | h1 :: h2 :: t -> read_vals ((int_of_string h1, float_of_string h2) :: acc) t
      | _ -> failwith "read_snow" in
    a.(n) <- read_vals [] (Str.split rxp s) in
  file_iter fname read;
  Array.get a
;;
