(* Setup TF-IDF: sym_num -> (int list -> unit) * (int -> float) * (unit -> float) *)
let setup_tfidf sym_num =
  let freq = Array.create sym_num 0 and a = Array.create sym_num 0. in
  let thn = ref 0 and thv = ref 0. in
  let add syms =
    List.iter (fun j -> freq.(j) <- freq.(j) + 1; a.(j) <- log (float_of_int freq.(j))) syms;
    incr thn; thv := log (float_of_int !thn)
  and get i = !thv -. a.(i)
  and get_sum () = float_of_int sym_num *. !thv -. Array.fold_left (fun sf s -> sf +. s) 0. a in
  (add, get, get_sum)
;;

