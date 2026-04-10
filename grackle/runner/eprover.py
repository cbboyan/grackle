from solverpy.solver.atp.eprover import E, E_BINARY, E_STATIC

from .solverpy import SolverPyRunner


E_FIXED_ARGS = "--delete-bad-limit=150000000 "

DEFAULTS = {
   "sel": "SelectMaxLComplexAvoidPosPred",
   "tord": "LPO4",
   "tord_prec": "arity",
   "tord_weight": "arity",
   "simparamod": "none",
   "srd": "0",
   "forwardcntxtsr": "0",
   "splaggr": "0",
   "splcl": "0",
   "tord_const": "0",
   "sine": "0",
   "defcnf": "24",
   "prefer": "0",
   "fwdemod": "2",
   "der": "none",
   "presat": "0",
   "condense": "0",
}

SINE_DEFAULTS = {
   "sineG": "CountFormulas",
   "sineh": "hypos",
   "sinegf": "1.2",
   "sineD": "none",
   "sineR": "none",
   "sineL": "100",
   "sineF": "1.0",
}

E_PROTO_ARGS = "%(splaggr)s%(srd)s%(forwardcntxtsr)s%(defcnf)s%(prefer)s%(presat)s%(condense)s%(splcl)s%(fwdemod)s%(der)s%(simparamod)s-t%(tord)s %(prord)s-W%(sel)s %(sine)s%(heur)s"

E_SINE_ARGS = "--sine='GSinE(%(sineG)s,%(sineh)s,%(sinegf)s,%(sineD)s,%(sineR)s,%(sineL)s,%(sineF)s)' "


def cef2block(cef):
   "Encode a CEF as a ParamILS string containg only [a-zA-Z0-9_]."
   return cef.replace("-","_M_").replace(",","__").replace(".","_D_").replace("(","__").replace(")","")

def block2cef(block):
   "Decode a CEF from a ParamILS string."
   parts = block.replace("_M_","-").replace("_D_",".").split("__")
   return "%s(%s)" % (parts[0], ",".join(parts[1:]))

def convert(params):
   # conversion from old ordering version
   if "prord" in params:
      params = dict(params)
      params["tord_prec"] = params["prord"]
      if params["tord"] == "KBO6":
         params["tord_weight"] = "invfreqrank"
         params["tord_const"] = "1"
      if params["tord"] == "WPO":
         params["tord_weight"] = "invfreqrank"
         params["tord_const"] = "1"
         params["tord_coefs"] = "constant"
         params["tord_algebra"] = "Sum"
      del params["prord"]
   # handle old sine version
   if "sine" in params and params["sine"] == "1":
      if params["sineR"] == "UU":
         params["sineR"] = "none"
      defaults = dict(SINE_DEFAULTS)
      defaults.update(params)
      params = defaults
   else:
      params["sine"] = "0"
   # add missing defaults
   defaults = dict(DEFAULTS)
   defaults.update(params)
   params = defaults
   return params


class EproverRunner(SolverPyRunner):

   RESOURCE_KEY = "Processed"

   def __init__(self, config={}):
      SolverPyRunner.__init__(self, config)
      self.default("penalty", 1000000)
      self.config["prefix"] = "eprover-"
      binary = self.config.get("ebinary") or E_BINARY
      static = self.config.get("eargs") or E_STATIC
      limit = self.config["timeout"]
      self._solver = E(limit=f"T{limit}", binary=binary, static=static)

   def args(self, params):
      eargs = dict(params)
      eargs = convert(eargs)

      def simple(arg, option):
         nonlocal eargs
         eargs[arg] = option if eargs[arg] == "1" else ""

      def direct(arg, option, none):
         nonlocal eargs
         if eargs[arg] == none:
            eargs[arg] = ""
         else:
            eargs[arg] = "%s=%s " % (option, eargs[arg])

      # simple binary flags (no value)
      simple("splaggr",        "--split-aggressive ")
      simple("srd",            "--split-reuse-defs ")
      simple("forwardcntxtsr", "--forward-context-sr ")
      simple("prefer",         "--prefer-initial-clauses ")
      simple("presat",         "--presat-simplify ")
      simple("condense",       "--condense ")

      # direct valued flags
      direct("defcnf",  "--definitional-cnf", "none")
      direct("splcl",   "--split-clauses",       "0")
      direct("fwdemod", "--forward-demod-level", "2")

      # destructive equality resolution
      if eargs["der"] == "std":
         eargs["der"] = "--destructive-er "
      elif eargs["der"] == "strong":
         eargs["der"] = "--destructive-er --strong-destructive-er "
      elif eargs["der"] == "agg":
         eargs["der"] = "--destructive-er --destructive-er-aggressive "
      elif eargs["der"] == "stragg":
         eargs["der"] = "--destructive-er --destructive-er-aggressive --strong-destructive-er "
      else: # should be "none"
         eargs["der"] = ""

      # paramodulation
      if eargs["simparamod"] == "normal":
         eargs["simparamod"] = "--simul-paramod "
      elif eargs["simparamod"] == "oriented":
         eargs["simparamod"] = "--oriented-simul-paramod "
      else: # should be "none"
         eargs["simparamod"] = ""

      # term ordering
      if eargs["tord"] == "KBO6":
         eargs["prord"] = "-G%(tord_prec)s -w%(tord_weight)s " % eargs
         if eargs["tord_const"] != "0":
            eargs["prord"] += "-c%(tord_const)s " % eargs
      elif eargs["tord"] == "LPO4":
         eargs["prord"] = "-G%(tord_prec)s " % eargs
      elif eargs["tord"] == "WPO":
         eargs["prord"] = "-G%(tord_prec)s -w%(tord_weight)s -A%(tord_coefs)s -a%(tord_algebra)s " % eargs
         if eargs["tord_const"] != "0":
            eargs["prord"] += " -c%(tord_const)s " % eargs
      else:
         eargs["prord"] = ""

      # SinE
      if eargs["sine"] == "1":
         for x in eargs:
            if x.startswith("sine") and eargs[x] == "none":
               eargs[x] = ""
         eargs["sine"] = E_SINE_ARGS % eargs
      else:
         eargs["sine"] = ""

      # given clause selection heuristic
      slots = int(eargs["slots"])
      cefs = []
      for i in range(slots):
         cefs += ["%s*%s" % (eargs["freq%d"%i], block2cef(eargs["cef%d"%i]))]
      cefs.sort(key=lambda x: int(x.split("*")[0]))
      eargs["heur"] = "-H'(%s)'" % ",".join(cefs)

      return E_FIXED_ARGS + (E_PROTO_ARGS % eargs)

   def clean(self, params):
      params = convert(params)

      if "slots" not in params:
         return None
      params = dict(params)
      slots = int(params["slots"])
      delete = []
      for param in params:
         if param.startswith("freq") or param.startswith("cef"):
            n = int(param.lstrip("freqcef"))
            if n >= slots:
               delete.append(param)

      if "sine" in params and params["sine"] == "0":
         delete.extend(SINE_DEFAULTS)

      if "prord" not in params:
         if params["tord"] == "Auto":
            delete.extend(["tord_prec", "tord_weight", "tord_const", "tord_algebra", "tord_coefs"])
         elif params["tord"] == "LPO4":
            delete.extend(["tord_weight", "tord_const", "tord_algebra", "tord_coefs"])
         elif params["tord"] == "KBO6":
            delete.extend(["tord_algebra", "tord_coefs"])

      for param in delete:
         if param in params:
            del params[param]

      return params
