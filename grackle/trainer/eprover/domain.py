from ..domain.grackle import GrackleDomain
from ..domain.multi import MultiDomain


# 20 predefined (freq, CEF) pairs for heuristic slot selection.
# Indexed 0-19; the EproverRunner maps indices back to these strings.
# Sources: nb7/new_bool (0-4), pre_casc/post_as_ho (5-7), HO-specific sh3/new_bool_8/new_ho (8-10),
#          mzr02 similarity weights / yan (11-17), mzr01/bls0f17 (18-19).
HEURISTIC_CEFS = [
    # 0-4: nb7 / new_bool family
    (2, "ConjectureRelativeSymbolWeight(PreferGround,0.5,100,100,100,100,1.5,1.5,1)"),
    (6, "ConjectureRelativeSymbolWeight(ByDerivationDepth,0.1,100,100,100,100,1.5,1.5,1.5)"),
    (1, "FIFOWeight(PreferProcessed)"),
    (1, "ConjectureRelativeSymbolWeight(PreferNonGoals,0.5,100,100,100,100,1.5,1.5,1)"),
    (2, "Refinedweight(PreferGoals,3,2,2,1.5,2)"),
    # 5-7: pre_casc / post_as_ho / eprover66 family
    (1, "ConjectureRelativeSymbolWeight(SimulateSOS,0.5,100,100,100,100,1.5,1.5,1)"),
    (4, "ConjectureRelativeSymbolWeight(ConstPrio,0.1,100,100,100,100,1.5,1.5,1.5)"),
    (4, "Refinedweight(SimulateSOS,3,2,2,1.5,2)"),
    # 8-10: HO-specific (sh3 / new_bool_8 / new_ho_11)
    (4, "ConjectureRelativeSymbolWeight(PreferFO,0.1,100,100,100,100,1.5,1.5,1.5)"),
    (1, "ConjectureRelativeSymbolWeight(PreferHOSteps,0.5,100,100,100,100,1.5,1.5,1)"),
    (1, "ConjectureRelativeSymbolWeight(PreferNonGoals,3,9999,4,3,5,4,4,2.5)"),
    # 11-17: mzr02 family (yan's similarity / prefix weight functions)
    (1, "ConjectureTermPrefixWeight(DeferSOS,1,3,0.1,5,0,0.1,1,4)"),
    (1, "ConjectureTermPrefixWeight(PreferNonGoals,1,3,100,9999.9,0,9999.9,3,5)"),
    (1, "StaggeredWeight(DeferSOS,1)"),
    (2, "StaggeredWeight(DeferSOS,2)"),
    (1, "SymbolTypeweight(DeferSOS,18,7,-2,5,9999.9,2,1.5)"),
    (2, "Clauseweight(PreferWatchlist,20,9999,4)"),
    (2, "ConjectureSymbolWeight(DeferSOS,9999,20,50,-1,50,3,3,0.5)"),
    # 18-19: mzr01 / bls0f17 family
    (1, "RelevanceLevelWeight2(ConstPrio,1,0,2,2,7,-1,2,0,0.2,9999.9,9999.9)"),
    (5, "Clauseweight(PreferUnitGroundGoals,7,9999,5)"),
]

N_CEFS = len(HEURISTIC_CEFS)  # 20


class EproverHeuristicDomain(GrackleDomain):
    """Clause selection heuristic: up to 4 slots, each picking one of N_CEFS predefined (freq, CEF) pairs."""

    @property
    def params(self):
        indices = [str(i) for i in range(N_CEFS)]
        return {
            "slots": ["1", "2", "3", "4"],
            "heur0": indices,
            "heur1": indices,
            "heur2": indices,
            "heur3": indices,
        }

    @property
    def defaults(self):
        return {
            "slots": "4",
            "heur0": "0",   # 2*CRSW(PreferGround,...)
            "heur1": "1",   # 6*CRSW(ByDerivationDepth,...)
            "heur2": "2",   # 1*FIFOWeight(PreferProcessed)
            "heur3": "3",   # 1*CRSW(PreferNonGoals,...)
        }

    @property
    def conditions(self):
        return [
            ("heur1", "slots", ["2", "3", "4"]),
            ("heur2", "slots", ["3", "4"]),
            ("heur3", "slots", ["4"]),
        ]


class EproverOrderingDomain(GrackleDomain):
    """Term ordering: type (LPO4/KBO6), precedence generation, weight generation (KBO only), HO order kind."""

    @property
    def params(self):
        return {
            "tord": ["LPO4", "KBO6"],
            "tord_prec": ["invfreq", "invfreqconjmax", "invfreqconstmin", "arity",
                          "invarity", "const_max", "freq", "invfreqrank"],
            "tord_weight": ["invfreqrank", "precrank10", "precrank20",
                            "arity", "aritymax0"],
            "tord_const": ["0", "1"],
            "ho_order_kind": ["lfho", "lambda"],
        }

    @property
    def defaults(self):
        return {
            "tord": "KBO6",
            "tord_prec": "invfreq",
            "tord_weight": "precrank10",
            "tord_const": "1",
            "ho_order_kind": "lfho",
        }

    @property
    def conditions(self):
        return [
            ("tord_weight", "tord", ["KBO6"]),
            ("tord_const", "tord", ["KBO6"]),
        ]


class EproverCoreDomain(GrackleDomain):
    """Core proof-search options: literal selection, inference control, simplification, HO extensions, SAT checking."""

    _SEL = [
        "SelectMaxLComplexAvoidAppVar",       # best for HO (nb7 family)
        "SelectComplexExceptUniqMaxHorn",     # FO-compatible (pre_casc, post_as_ho1)
        "PSelectComplexExceptUniqMaxHorn",    # HO-specific (new_ho_11, sh6)
        "SelectMaxLComplexAPPNTNp",           # HO (sh5, sh5l)
        "SelectMaxLComplexAvoidPosPred",      # FO classic (mzr05, bls)
        "SelectNewComplexAHP",                # FO (bls0222)
        "SelectComplexG",                     # FO (mzr01, mzr10)
        "SelectCQIPrecWNTNp",                 # FO (eprover66)
        "SelectNoLiterals",                   # baseline
    ]

    @property
    def params(self):
        return {
            # Literal selection
            "sel": self._SEL,
            # Paramodulation
            "simparamod": ["none", "normal", "oriented"],
            # Destructive ER
            "der": ["none", "std", "strong", "agg", "stragg"],
            # Simplification
            "forwardcntxtsr": ["0", "1"],
            "fwdemod": ["0", "1", "2"],
            "condense": ["0", "1"],
            "presat": ["0", "1"],
            "prefer": ["0", "1"],
            # Splitting
            "splaggr": ["0", "1"],
            "srd": ["0", "1"],
            "splcl": ["0", "4", "7"],
            # Preprocessing
            "defcnf": ["none", "0", "3", "4", "6", "8", "12", "24"],
            "strong_rw_inst": ["0", "1"],
            "no_eq_unfolding": ["0", "1"],
            "sos_input_types": ["0", "1"],
            # SAT checking
            "satcheck": ["none", "ConjMinMinFreq"],
            # HO extension rules
            "neg_ext": ["off", "all"],
            "pos_ext": ["off", "all"],
            "ext_sup_max_depth": ["-1", "0", "1"],
            # HO lambda handling
            "lift_lambdas": ["true", "false"],
            "local_rw": ["false", "true"],
            "fool_unroll": ["true", "false"],
            # HO injectivity
            "inverse_recognition": ["false", "true"],
            "replace_inj_defs": ["false", "true"],
        }

    @property
    def defaults(self):
        # Defaults match the nb7/new_bool_7 strategy profile
        return {
            "sel": "SelectMaxLComplexAvoidAppVar",
            "simparamod": "normal",
            "der": "stragg",
            "forwardcntxtsr": "1",
            "fwdemod": "1",
            "condense": "1",
            "presat": "1",
            "prefer": "0",
            "splaggr": "0",
            "srd": "0",
            "splcl": "0",
            "defcnf": "4",
            "strong_rw_inst": "1",
            "no_eq_unfolding": "1",
            "sos_input_types": "1",
            "satcheck": "ConjMinMinFreq",
            "neg_ext": "all",
            "pos_ext": "all",
            "ext_sup_max_depth": "0",
            "lift_lambdas": "false",
            "local_rw": "true",
            "fool_unroll": "false",
            "inverse_recognition": "false",
            "replace_inj_defs": "false",
        }


class EproverSineDomain(GrackleDomain):
    """SinE axiom selection parameters."""

    @property
    def params(self):
        return {
            "sine": ["0", "1"],
            "sineG": ["CountFormulas", "CountTerms"],
            "sineh": ["none", "hypos"],
            "sinegf": ["1.0", "1.1", "1.2", "1.4", "1.5", "2.0", "5.0", "6.0"],
            "sineD": ["none", "1", "3", "10", "20", "40", "160"],
            "sineR": ["none", "01", "02", "03", "04"],
            "sineL": ["10", "20", "40", "60", "80", "100", "500", "20000"],
            "sineF": ["1.0", "0.8", "0.6"],
        }

    @property
    def defaults(self):
        return {
            "sine": "1",
            "sineG": "CountFormulas",
            "sineh": "hypos",
            "sinegf": "1.2",
            "sineD": "none",
            "sineR": "none",
            "sineL": "100",
            "sineF": "1.0",
        }

    @property
    def conditions(self):
        return [
            ("sineG",  "sine", ["1"]),
            ("sineh",  "sine", ["1"]),
            ("sinegf", "sine", ["1"]),
            ("sineD",  "sine", ["1"]),
            ("sineR",  "sine", ["1"]),
            ("sineL",  "sine", ["1"]),
            ("sineF",  "sine", ["1"]),
        ]


class EproverDomain(MultiDomain):
    """Default E prover domain: core + ordering + heuristic (without SinE)."""

    def __init__(self):
        MultiDomain.__init__(self, domains=[
            EproverCoreDomain(),
            EproverOrderingDomain(),
            EproverHeuristicDomain(),
        ])
