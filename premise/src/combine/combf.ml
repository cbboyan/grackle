open Utils;;
open Format;;

let avg  xw x yw y zw z ww w = xw *. x +. yw *. y +. zw *. z +. ww *. w;;
let geo  xw x yw y zw z ww w = (x ** xw) *. (y ** yw) *. (z ** zw) *. (w ** ww);;
let minf xw x yw y zw z ww w =
  let x = if xw = 0. then 1000000. else x /. xw
  and y = if yw = 0. then 1000000. else y /. yw
  and z = if zw = 0. then 1000000. else z /. zw
  and w = if ww = 0. then 1000000. else w /. ww in
  min (min x y) (min z w);;
let maxf xw x yw y zw z ww w = max (max (xw *. x) (yw *. y)) (max (zw *. z) (ww *. w));;
let har  xw x yw y zw z ww w = 1. /. ((xw /. x) +. (yw /. y) +. (zw /. z) +. (ww /. w));;
let qua  xw x yw y zw z ww w = xw *. x *. x +. yw *. y *. y +. zw *. z *. z +. ww *. w *. w;;

let f2f = function
  "avg" -> avg | "geo" -> geo | "min" -> minf | "max" -> maxf | "har" -> har | "qua" -> qua
| _ -> failwith "unkonwn";;

let (n1,f1,n2,f2,n3,f3,n4,f4,eval,avg,maxv,seqf) = match Sys.argv with
  [|_;n1;f1;n2;e;a;m;sf|] -> let f1 = float_of_string f1 in (n1,f1,n2,1.-.f1,"",0.,"",0.,e,f2f a,int_of_string m,sf)
| [|_;n1;f1;n2;f2;n3;e;a;m;sf|] -> let f1,f2 = float_of_string f1,float_of_string f2 in
                            (n1,f1,n2,f2,n3,1.-.f1-.f2,"",0.,e,f2f a,int_of_string m,sf)
| [|_;n1;f1;n2;f2;n3;f3;n4;e;a;m;sf|] -> let f1,f2,f3 = float_of_string f1,float_of_string f2,float_of_string f3 in
      (n1,f1,n2,f2,n3,f3,n4,1.-.f1-.f2-.f3,e,f2f a,int_of_string m,sf)
| _ -> failwith "Usage: combf dep1 f1 dep2 [f2 dep3 [f3 dep4]] eval avg maxv seq";;

let (th_no, no_th, th_num) = read_order seqf 150000;;
let th_num_iter f = for i = 0 to th_num - 1 do f i done;;
let deps1 = if f1>0. then read_deps n1 th_num th_no else (fun _ -> []);;
let deps2 = if f2>0. then read_deps n2 th_num th_no else (fun _ -> []);;
let deps3 = if f3>0. then read_deps n3 th_num th_no else (fun _ -> []);;
let deps4 = if f4>0. then read_deps n4 th_num th_no else (fun _ -> []);;

let hashnos h s =
  let v = ref 0 in
  List.iter (fun t -> (if !v < maxv then incr v); Hashtbl.add h t !v) s;;

let vote i =
  let h1, h2, h3, h4 = Hashtbl.create maxv, Hashtbl.create maxv,
    Hashtbl.create maxv, Hashtbl.create maxv in
  hashnos h1 (deps1 i); hashnos h2 (deps2 i); hashnos h3 (deps3 i); hashnos h4 (deps4 i);
  let initf j =
    let v1 = try Hashtbl.find h1 j with Not_found -> maxv
    and v2 = try Hashtbl.find h2 j with Not_found -> maxv
    and v3 = try Hashtbl.find h3 j with Not_found -> maxv
    and v4 = try Hashtbl.find h4 j with Not_found -> maxv in
    avg f1 (float_of_int v1) f2 (float_of_int v2) f3 (float_of_int v3) f4 (float_of_int v4)
  in
  let votes = Array.init i (fun j -> (j, initf j)) in
  heapsort (fun a b -> compare (snd b) (snd a)) maxv votes;
  let rec ret acc at =
    if at = Array.length votes then acc else ret (fst votes.(at) :: acc) (at + 1) in
  ret [] (max 0 (Array.length votes - maxv))
;;

let to_eval = Hashtbl.create 100000;;
file_iter eval (fun n s -> Hashtbl.add to_eval (th_no s) ());;
let print_eval oc i lst =
  os oc (no_th i); os oc ":";
  oiter oc (fun d -> os oc (no_th d)) " " lst; os oc "\n"; flush oc;;
let do_vote i = if Hashtbl.mem to_eval i then print_eval stdout i (vote i);;
th_num_iter do_vote;;
