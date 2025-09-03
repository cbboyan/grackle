import os
from solverpy.solver.smt.z3 import Z3

from .. import log
from .runner import GrackleRunner
from ..trainer.z3.options import OptionsDomain
from ..trainer.z3.tactics import TACTICS, BOOLS, DEPTHS

def options(params, i, name, typ, defs):
   if name not in defs:
      return []
   opts = []
   for (n,arg) in enumerate(defs[name]):
      param = f"t__t{i}__{typ}{n}"
      assert param in params
      opts.append(f":{arg} {params[param]}")
   return opts

def tactic(params, i):
   master = f"t__t{i}" 
   assert master in params
   name = TACTICS[int(params[master])]
   opts = []
   opts.extend(options(params, i, name, "bool", BOOLS)) 
   opts.extend(options(params, i, name, "depth", DEPTHS))
   if opts:
      return f"(or-else (using-params {name} {' '.join(opts)}) skip)"
   else:
      return f"(or-else {name} skip)"

def tactical(params):
   if "t__count" not in params:
      return None
   n_count = int(params["t__count"])
   ts = []
   for i in range(n_count):
      ts.append(tactic(params, i))
   if not ts:
      return None
   ts.append("smt")
   return f"(then {' '.join(ts)})"

class Z3Runner(GrackleRunner):
   
   def __init__(self, config={}):
      GrackleRunner.__init__(self, config)
      self.default("penalty", 100000000)
      penalty = self.config["penalty"]
      self.default("penalty.error", penalty*1000)
      self.default_domain(OptionsDomain)
      #self.conds = self.conditions(CONDITIONS)

      limit = self.config["timeout"]
      self._z3 = Z3(limit=f"T{limit}-M4", complete=False)

   def args(self, params):
      options = []
      for x in params:
         if not x.startswith("t__"):
            options.append(f"(set-option :{x} {params[x]})")
      options = "\n".join(options)
      assert self.domain
      tac = tactical(self.domain.defaults | params)
      if tac is None:
         return options
      else:
         return f"{options}\n\n;(check-sat-using {tac})"
   
   def run(self, entity, inst):
      params = entity if self.config["direct"] else self.recall(entity)
      strat = self.args(params)
      problem = os.path.join(os.getenv("PYPROVE_BENCHMARKS", "."), inst)
      try:
         result = self._z3.solve(problem, strat)
      except Exception:
         result = {}
      if not self._z3.valid(result):
         msg = "\nERROR(Grackle): Error while evaluating on instance %s!\ncommand: %s\nparams: %s\noutput: \n%s\n"%(inst,strat,self.repr(params),self._z3._output)
         log.fatal(msg)
         return None
      ok = self._z3.solved(result)
      status = result["status"]
      runtime = result["runtime"]
      quality = 10+int(1000*runtime) if ok else self.config["penalty"]
      resources = result["rlimit-count"] if "rlimit-count" in result else quality
      return [quality, runtime, status, resources]

   def success(self, result):
      return result in self._z3.success
