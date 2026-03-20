# SimpleTasks Feature — Design Spec
## OPI (ORCA Python Interface)

This document is the authoritative design spec for the `SimpleTasks` feature.
Feed it to a Claude Code agent at the start of each implementation session.

---

## Overview

SimpleTasks adds a high-level abstraction layer to OPI so users can run common
quantum chemistry tasks without needing to know ORCA input syntax. Instead of
manually assembling `SimpleKeyword` objects and `Input` objects, users just
specify a method, basis set, and task type.

**Target usage:**
```python
from opi.simple_tasks import SinglePointTask, OptTask

structure = Structure.from_smiles("O")

sp = SinglePointTask(method="BP86", basis_set="SV(P)")
result = sp.run(basename="water_sp", structure=structure, working_dir=Path("water_sp"))
energy = result.primary_property  # float, in Hartree

opt = OptTask(method="GFN2-xTB")  # SQM - no basis needed
result = opt.run(basename="water_opt", structure=structure, working_dir=Path("water_opt"))
energy, optimised_structure = result.primary_property  # tuple[float, Structure]
```

---

## Package location

```
src/opi/simple_tasks/
├── __init__.py        # public exports
├── base.py            # Task, TaskCompleted base classes
├── method_params.py   # DftParams, SqmParams, WftParams + method family registry
├── tasks.py           # SinglePointTask, OptTask, EnGradTask
└── results.py         # SinglePointCompleted, OptCompleted, EnGradCompleted
```

---

## Class hierarchy

```
Task  (base)                  TaskCompleted  (base)
├── SinglePointTask           ├── SinglePointCompleted  → primary_property: float
├── OptTask                   ├── OptCompleted          → primary_property: tuple[float, Structure]
└── EnGradTask                └── EnGradCompleted       → primary_property: tuple[float, tuple[float, ...]]
```

---

## Detailed design decisions

### `Task` base class (`base.py`)

- **Plain Python class — NOT a Pydantic model**
- Constructor accepts:
  - `method: str | SimpleKeyword`
  - `basis_set: str | SimpleKeyword | None = None` (None is valid for SQM/FF)
- Both `method` and `basis_set` are **normalised to `SimpleKeyword` at construction time**:
  - Try `Method.find_keyword(method)` to resolve against known keywords
  - If `ValueError` (unknown method): wrap as `SimpleKeyword(method)` and emit
    `warnings.warn(f"'{method}' is not a recognised method in OPI. Treating as-is.")`
  - Same pattern for `basis_set` using `BasisSet.find_keyword()`
- **Auto-detects method family** (DFT / SQM / WFT / FF) from a central registry
  in `method_params.py`. Unknown methods default to DFT with a warning.
- **JIT Input construction** — parameters stored as plain attributes on `self`.
  The `Input` object is only assembled when `get_input()` is called (i.e. at
  `run()` time), never at construction time. This makes mutation trivial:
  ```python
  sp.method = SimpleKeyword("PBE0")  # just changes an attribute
  result = sp.run(...)               # Input built fresh from current state
  ```
- **`Task` is a factory — stateless w.r.t. runs.** Calling `run()` multiple
  times returns independent `TaskCompleted` objects. No state is written back
  to `self` after `run()`.
- Exposes two public helper methods:
  - `get_input() -> Input` — builds and returns the configured Input object
  - `get_calculator(basename, structure, working_dir) -> Calculator` — returns
    a fully configured Calculator ready to run

### `Task.run()` signature

```python
def run(
    self,
    basename: str,
    structure: Structure,
    working_dir: Path | None = None,
    ncores: int | None = None,
    memory_per_core: int | None = None,
    force: bool = False,
    reuse_completed: bool = False,
) -> "TaskCompleted": ...
```

### `run()` guard behaviour (important — implement carefully)

- If `working_dir` does **not** exist → proceed normally
- If `working_dir` exists and `force=False` and `reuse_completed=False`
  → raise `RuntimeError` with a clear message
- If `working_dir` exists and `force=True`
  → overwrite (mirrors `Calculator.write_input(force=True)`)
- If `working_dir` exists and `reuse_completed=True`:
  - Check BOTH: `.property.json` exists AND `Output.terminated_normally()` is `True`
  - If yes → skip execution, return `TaskCompleted` built from existing files
  - If no (files exist but job incomplete/failed) → raise `RuntimeError`
  - Do NOT just check for file existence — a failed run also leaves files behind

### `TaskCompleted` base class (`base.py`)

- `calculator: Calculator` — stored for restarting
- `get_output() -> Output` — escape hatch to full Output object
- `status: bool` — job terminated normally AND task-specific convergence reached
- `primary_property` — abstract, typed and documented per subclass

---

### Method family params (`method_params.py`)

- `DftParams`, `SqmParams`, `WftParams`, `ForceFieldParams` are **`TaskParams`
  subclasses** (Pydantic `BaseModel` via `TaskParams`)
- The **user never imports or instantiates these directly** — they are
  auto-selected internally by `get_params_for_method()`
- **No hardcoded registry dict.** Family detection uses the OPI keyword class
  hierarchy: `Dft.find_keyword()`, `Wft.find_keyword()`, `Sqm.find_keyword()`,
  `ForceField.find_keyword()` are tried in order. This stays automatically in
  sync as new keywords are added to OPI.
  - `Dft`, `Wft`, `Sqm`, `ForceField` are all direct subclasses of `Method`
    (see `src/opi/input/simple_keywords/`)
  - Unknown methods warn and default to `DftParams`
- `Task.get_input()` already adds `method` and `basis_set` as simple keywords
  before calling `map_to_input()`. Params classes must NOT re-add those — they
  only handle family-specific extras (dispersion, RI, block options, …).
- All four params classes are **currently fieldless stubs**. They carry no
  `Annotated` fields yet because no family-specific extras are implemented.
  `get_params_for_method()` instantiates them with no arguments: `DftParams()`.
- `DftParams` — stub; requires explicit `basis_set` on the Task
- `SqmParams` — stub; no basis set needed (implicit in the method)
- `WftParams` — stub; requires explicit `basis_set` on the Task
- `ForceFieldParams` — stub; no basis set needed
- Each has `map_to_input(input_object: Input) -> Input` inherited from `TaskParams`.
  The `Annotated` metadata pattern for future field extensions is documented in
  `TaskParams` (in `src/opi/simple_tasks/base.py`).
  `simple_task_pr_task_base.py` no longer exists — its content was merged into `base.py`.
- **3c composite methods** (`r2scan-3c`, `b97-3c`, `pbeh-3c`, …) are out of scope
  for the initial implementation and not handled specially.

---

### Concrete result classes (`results.py`)

```python
class SinglePointCompleted(TaskCompleted):
    @property
    def primary_property(self) -> float:
        """Final single-point energy in Hartree."""
        ...

class OptCompleted(TaskCompleted):
    @property
    def primary_property(self) -> tuple[float, Structure]:
        """(energy_hartree, optimised_structure)"""
        ...

class EnGradCompleted(TaskCompleted):
    @property
    def primary_property(self) -> tuple[float, tuple[float, ...]]:
        """(energy_hartree, gradient) where gradient is a flat tuple
        of Cartesian components (x,y,z per atom) in Eh/Bohr."""
        ...
```

---

### Concrete task classes (`tasks.py`)

```python
class SinglePointTask(Task):
    def run(self, ...) -> SinglePointCompleted: ...

class OptTask(Task):
    def run(self, ...) -> OptCompleted: ...

class EnGradTask(Task):
    def run(self, ...) -> EnGradCompleted: ...
```

Each subclass narrows the return type of `run()`. The actual implementation
of `run()` lives on the base `Task` class — subclasses just override the
return type annotation and instantiate the correct `TaskCompleted` subclass.

**Implementation notes (already in code):**
- Each subclass overrides `get_input()` to call `super().get_input()` then
  appends the ORCA task keyword (`OrcaTask.SP` / `OrcaTask.OPT` /
  `OrcaTask.ENGRAD`).
- `opi.input.simple_keywords.task.Task` is imported as `OrcaTask` to avoid
  a name collision with `simple_tasks.base.Task`.
- `_make_completed(calculator)` is the abstract hook called by `Task.run()`.
  Subclasses implement it to return the correct `TaskCompleted` subclass.
- `run()` overrides use `typing.cast` to satisfy mypy's covariant return type
  without duplicating logic. No `# type: ignore` needed.

---

### `__init__.py` public exports

```python
from opi.simple_tasks.tasks import SinglePointTask, OptTask, EnGradTask
from opi.simple_tasks.results import SinglePointCompleted, OptCompleted, EnGradCompleted
from opi.simple_tasks.base import Task, TaskCompleted, TaskParams
```

---

## OPI patterns to follow

- Type safety throughout — use mypy-compatible annotations everywhere
- `SimpleKeyword` and `SimpleKeywordBox` for all ORCA keywords
- Method keyword hierarchy: `Method` (base) → `Dft`, `Wft`, `Sqm`, `ForceField`
  (all in `src/opi/input/simple_keywords/`). `Function` no longer exists.
- `Method.find_keyword(s)` resolves string → `SimpleKeyword`, raises `ValueError` if unknown.
  `Dft.find_keyword(s)` restricts the lookup to DFT keywords only, etc.
- `Calculator.write_input(force=)` is the existing overwrite pattern being mirrored
- NumPy-style docstrings on all public classes and methods
- No underscores in module names (OPI convention)
- Pydantic used for data/param classes, plain Python for actor/behaviour classes
- `mypy`, `ruff`, `codespell` must pass
- Run unit tests via `uv run nox -s unit_tests` (CI-safe, no ORCA required)
- Run mypy via `uv run nox -s type_check`
- `Input.has_blocks()` takes `Block` **instances**, not types — pass the
  already-constructed instance when checking block existence
- `SimpleKeywordBox.from_string` / `registry` / `__init_subclass__` in
  `src/opi/input/simple_keywords/base.py` required type annotations to pass
  mypy; fixed in this feature branch

## Out of scope for initial implementation

- Solvent / solvent model
- RI basis set
- Dispersion correction
- `FreqTask`, `GoatTask`
- Async execution
- Multi-node / cluster support
- 3c composite methods (`r2scan-3c`, `b97-3c`, `pbeh-3c`, `hf-3c`, …)
