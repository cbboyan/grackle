open Utils;;
open Format;;

let (pred, deps, seq) = match Sys.argv with
  [|_; p; d; s|] -> (p, d, s)
| _ -> failwith "Usage: recall predictions deps seq";;

let (th_no, no_th, th_num) = read_order seq 150000;;
let deps = read_deps deps th_num th_no;;

(* Numbers for which to compute the graphs, uncomment one of these lines. *)

(*let pow2 = [|1; 2; 4; 6; 8; 11; 16; 23; 32; 45; 64; 91; 128; 181; 256; 362; 512; 724; 1024; 1448; 2048|] *)
let pow2 = Array.init 200 (fun i -> i + 1);;

(* Arrays for values for the graph points: Full-Recall-i and Cover-i *)
let pow2c = Array.create (Array.length pow2) 0;;
let cow2c = Array.create (Array.length pow2) 0.0;;

let update_pows depsh depslen pred =
  let update_pow i pw =
    let hash = Hashtbl.copy depsh in
    let cutpred = cut_list [] pw pred in
    List.iter (Hashtbl.remove hash) cutpred;
    if Hashtbl.length hash = 0 then pow2c.(i) <- pow2c.(i) + 1;
    (* There are two possible formulas for computing the cover: one that does the division by the number of dependencies, the other considers that the number of predictions may be smaller than the number of dependencies, and divides by the minimum *)
(*    cow2c.(i) <- cow2c.(i) +. (float_of_int (depslen - Hashtbl.length hash) /. float_of_int (depslen))*)
    cow2c.(i) <- cow2c.(i) +. (float_of_int (depslen - Hashtbl.length hash) /. float_of_int (min depslen pw))
  in
  Array.iteri update_pow pow2
;;

(*
|used \inter n highers ranked|
------
|used|
*)

let prec100, cover100, recall, avrank, auc, preds, depno, nos = ref 0, ref 0., ref 0, ref 0., ref 0., ref 0, ref 0, ref 0;;

let pred_line n h ds =
  let curth = th_no h in
  let deps = deps curth in
  if deps <> [] then
  begin
    let depslen = List.length deps in
    let depsh = list_to_hash depslen deps in
    let pred = List.map th_no ds in
    (*Printf.eprintf "%i\n" (List.length pred);*)
    let pred, badpred = List.partition (fun x -> x < curth) pred in
    if badpred <> [] then failwith "Future predictions make for incorrect statistics!";
    let predlen = List.length pred in
    update_pows depsh depslen pred;
    (* Cover = how much of the whole training set do we cover in first 100 suggestions *)
    let pred100 = cut_list [] 100 pred in
    let pred100h = list_to_hash 100 pred100 in
    let cov = float_of_int (List.length (List.filter (Hashtbl.mem pred100h) deps)) in
    cover100 := !cover100 +. cov /. (float_of_int depslen);
    (* Prec = how many of first 100 suggestions are from the training set *)
    prec100 := !prec100 + List.length (List.filter (Hashtbl.mem depsh) pred100);
    (* FullRecall = minimum number of preds to cover the training set or predlen+1 if never *)
    let (td, recal) = List.fold_left (fun (todel, sf) e -> if todel = 0 then (todel, sf) else
      if Hashtbl.mem depsh e then (todel - 1, sf + 1) else (todel, sf + 1)) (depslen, 0) pred in
    recall := !recall + (if td = 0 then recal else predlen + 1);
    (* Average rank *)
    let (_, missed, ar) = List.fold_left (fun (pos, todel, sf) e ->
      if Hashtbl.mem depsh e then (pos + 1, todel - 1, sf + pos) else (pos + 1, todel, sf)) (0, depslen, 0) pred in
    avrank := !avrank +. (float_of_int (ar + missed * predlen)) /. float_of_int depslen;
    (* AUC *)
    let neg = List.fold_left (fun n e -> if Hashtbl.mem depsh e then n else n + 1) 0 pred in
    let (pos, neg, asum) = List.fold_left (fun (p, n, a) e ->
    (*if Hashtbl.mem depsh e then (p + 1, n, a + p) else (p, n + 1, a + p)) (0,0,0) pred in *)
      if Hashtbl.mem depsh e then (p + 1, n, a + (neg - n)) else (p, n + 1, a)) (0,0,0) pred in
    (* Maybe should be pos rather than depslen *)
    (*let aucc = if pos = 0 || neg = 0 then 1.0 else float_of_int asum /. float_of_int (pos * neg) in*)
    let aucc = if pos = 0 || neg = 0 then 1.0 else float_of_int asum /. float_of_int (pos * neg) in
    auc := !auc +. aucc;
    preds := !preds + predlen;
    depno := !depno + depslen;
    incr nos
  end
;;
dep_file_iter pred pred_line;;

Printf.printf "%s\t Cov: %.3f\t Prec: %.3f\t Rec: %.2f\t Auc: %.4f\t Rank: %.2f\t Avg: %.2f\n"
 (*"Dep: %.4f No: %i\n"*) pred
  (!cover100 /. float_of_int !nos)
  ((float_of_int !prec100) /. (float_of_int !nos))
  ((float_of_int !recall) /. (float_of_int !nos))
  (!auc /. (float_of_int !nos))
  (!avrank /. (float_of_int !nos))
(*  ((float_of_int !preds) /. (float_of_int !nos))*)
  ((float_of_int !depno) /. (float_of_int !nos)) (*!nos*);;
Array.iter (fun i -> Printf.printf "%i " i) pow2c;;
print_char '\n';;
Array.iter (fun i -> Printf.printf "%.2f " (100. *. i /. (float_of_int !nos))) cow2c;;
print_char '\n';;
