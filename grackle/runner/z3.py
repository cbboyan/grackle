import os
from solverpy.solver.smt.z3 import Z3

from .. import log
from .runner import GrackleRunner
from ..trainer.z3.default import DefaultDomain

class Z3Runner(GrackleRunner):
   
   def __init__(self, config={}):
      GrackleRunner.__init__(self, config)
      self.default("penalty", 100000000)
      penalty = self.config["penalty"]
      self.default("penalty.error", penalty*1000)
      self.default_domain(DefaultDomain)
      #self.conds = self.conditions(CONDITIONS)

      limit = self.config["timeout"]
      self._z3 = Z3(limit=f"T{limit}-M4", complete=False)

   def args(self, params):
      prefix = []
      for x in params:
         prefix.append(f"(set-option :{x} {params[x]})")
      return "\n".join(prefix)
   
   def run(self, entity, inst):
      params = entity if self.config["direct"] else self.recall(entity)
      strat = self.args(params)
      problem = os.path.join(os.getenv("PYPROVE_BENCHMARKS", "."), inst)
      try:
         result = self._z3.solve(problem, strat)
      except Exception:
         result = {}
      if not self._z3.valid(result):
         msg = "\nERROR(Grackle): Error while evaluating on instance %s!\ncommand: %s\nparams: %s\noutput: \n%s\n"%(inst,strat,self.repr(params),"-")
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

   def clean(self, params):
      params = {x:params[x] for x in params if params[x] != self.domain.defaults[x]}
      return params
