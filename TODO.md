# TODO

Migration plan towards `solverpy-grackle` in the solverpy monorepo.

## 1. Remove CVC4

- [x] Delete `grackle/runner/cvc4.py`
- [x] Delete `grackle/trainer/cvc4/`

## 2. Migrate runners to solverpy

Add `grackle/runner/solverpy.py` with `SolverPyRunner(GrackleRunner)` — a generic base
that implements `run()` and `success()` using `self._solver` (a solverpy instance) and
a `RESOURCE_KEY` class attribute.  Subclasses only need to set `self._solver` in
`__init__` and implement `args()`.

Also: replace `PYPROVE_BENCHMARKS` with `SOLVERPY_BENCHMARKS` everywhere; replace
`pyprove:` benchmark prefix in `state.py` with `solverpy:` using `bids.problems()`.

- [x] Add `SolverPyRunner` base class (`grackle/runner/solverpy.py`)
- [x] Refactor `Z3Runner` onto `SolverPyRunner`
- [x] Rewrite `EproverRunner` — use `solverpy.solver.atp.eprover.E`; drop `pyprove` dependency
- [x] Rewrite `LashRunner` — use `solverpy.solver.atp.lash.Lash`
- [x] Rewrite `VampireRunner` — use `solverpy.solver.atp.vampire.Vampire`
- [x] Rewrite `Cvc5Runner` — use `solverpy.solver.smt.cvc5.Cvc5`

## 3. Tests for runners

- [x] `tests/test_runner_eprover.py` — 29 tests: `args()`, `clean()`, `success()`, `run()` with mocked solver
- [x] `tests/test_runner_z3.py` — 28 tests: `args()`, `tactical()`, `success()`, `run()` with mocked solver
- [x] `tests/test_runner_lash.py` — 22 tests
- [x] `tests/test_runner_vampire.py` — 23 tests
- [x] `tests/test_runner_cvc5.py` — 25 tests

## 4. Migrate trainer domains to GrackleDomain

Use `grackle/trainer/z3/options.py` as the template. Replace raw-string `PARAMS/CONDITIONS/FORBIDDENS` dicts with a proper `GrackleDomain` subclass.

- [ ] Migrate `trainer/lash/domain.py`
- [ ] Migrate `trainer/vampire/` (consolidate or keep `domain.py`, `domain_full.py`, `domain_casc.py` variants as separate classes)
- [ ] Migrate `trainer/cvc5/` (consolidate or keep `domain_base/regular/uf/all` variants)
- [ ] Migrate `trainer/bitwuzla/domain.py` (runner already has `DefaultDomain`; align trainer)
- [ ] Rewrite `trainer/eprover/` — new `GrackleDomain` subclasses + `MultiDomain` for staged tuning

## 5. Add RamParILS trainer

Add `grackle/trainer/ramparils.py` as a drop-in alternative to `ParamilsTrainer`:
- Use `ramparils.specialize(strategy, scenario, cache_db, cores)` Python API
- Same interface as `ParamilsTrainer` (`improve(state, conf, insts)`)
- Add `RamparilsStageTrainer` alongside `ParamilsStageTrainer`

## 6. Migrate evaluation to solverpy

Replace the current `Runner.runs()` multiprocessing pool with solverpy's evaluation pipeline (`solverpy.benchmark.evaluation`):

- Use `evaluation.run(job, talker, db, cores)` where `job = (solver, bid, sid)`
- `direct=True` → no `Sid` plugin on the solver (strategy string passed directly)
- `direct=False` → add `Sid` plugin (`solverpy.solver.plugins.db.sid.Sid`) so the solver loads strategy content from `solverpy_db/strats/` by sid
- Result caching moves from grackle's `db.py` JSON files to solverpy's `solverpy_db/` providers

## 7. YAML scenario files

- Replace INI-style `.fly` parsing (`tools.py:parse_ini()`) with YAML
- Update `bin/fly-grackle.py` entry point
- Update examples in `examples/`

## 8. Type annotations

- Add type hints throughout, following solverpy's style (see `~/repos/cbboyan/solverpy/CLAUDE.md`)

## 9. Migrate to solverpy monorepo

- Move package into `~/repos/cbboyan/solverpy` as `packages/solverpy-grackle/`
- Update imports, `setup.py` / `pyproject.toml`, and CI

## 10. Documentation

- Docs will be unified with solverpy's existing `mkdocs` site (same pattern as `solverpy-learn`)
- Add docstrings and integrate into solverpy's `mkdocs-build.sh` / `mkdocs-deploy.sh` workflow
