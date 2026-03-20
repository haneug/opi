# SimpleTasks — Agent Session Prompts
## One prompt per file, use in order

Paste the relevant section below at the start of each Claude Code session,
together with `simple_tasks_design_spec.md`.

---

## Session 1 — `base.py`

```
I am implementing the SimpleTasks feature for OPI (ORCA Python Interface).
Please read the attached design spec: simple_tasks_design_spec.md

Also read these existing OPI files for context:
- src/opi/core.py              (Calculator class)
- src/opi/output/core.py       (Output class)
- src/opi/input/core.py        (Input class)
- src/opi/input/simple_keywords/base.py  (SimpleKeyword, SimpleKeywordBox)

Now implement src/opi/simple_tasks/base.py containing:
- Task base class (plain Python, not Pydantic)
- TaskCompleted base class

Pay special attention to:
- The reuse_completed guard must check BOTH file existence AND
  Output.terminated_normally() — not just file existence
- Task is a factory: run() must not write any state back to self
- JIT Input construction: no Input object is created in __init__

Do not implement method_params.py, tasks.py, results.py yet.
When done, summarise any assumptions you made that will affect the next files.
```

---

## Session 2 — `method_params.py`

```
I am implementing the SimpleTasks feature for OPI (ORCA Python Interface).
Please read the attached design spec: simple_tasks_design_spec.md

Also read these existing OPI files for context:
- src/opi/input/core.py                  (Input class)
- src/opi/input/simple_keywords/base.py  (SimpleKeyword, SimpleKeywordBox)
- src/opi/input/simple_keywords/method.py  (Method — parent of Dft, Wft, Sqm, ForceField)
- src/opi/input/simple_keywords/dft.py   (Dft — subclass of Method)
- src/opi/input/simple_keywords/wft.py   (Wft — subclass of Method)
- src/opi/input/simple_keywords/sqm.py   (Sqm — subclass of Method)
- src/opi/input/simple_keywords/force_field.py  (ForceField — subclass of Method)
- src/opi/input/blocks/base.py           (Block base class)

Also read the already implemented file:
- src/opi/simple_tasks/base.py           (TaskParams with Annotated metadata pattern is HERE
                                          — simple_task_pr_task_base.py no longer exists)

Now implement src/opi/simple_tasks/method_params.py containing:
- DftParams, SqmParams, WftParams, ForceFieldParams as TaskParams subclasses
- Each with a method: SimpleKeyword field (plain, not Annotated — Task.get_input() already
  adds method and basis_set keywords before calling map_to_input)
- get_params_for_method(method: SimpleKeyword) -> TaskParams using class-hierarchy lookup:
    try Dft.find_keyword(), Wft.find_keyword(), Sqm.find_keyword(), ForceField.find_keyword()
    in order — return the matching params class; warn + default to DftParams for unknowns
- A resolve_method_family(method: str) -> str helper
- ForceFieldParams is a stub for now (method field only, no basis_set)
- No hardcoded METHOD_FAMILY_REGISTRY dict — use the class hierarchy instead

The Annotated metadata pattern for future field extensions is documented in
TaskParams (src/opi/simple_tasks/base.py).
Users never import these classes directly.

When done, summarise any assumptions made that will affect results.py / tasks.py.
```

---

## Session 3 — `results.py`

```
I am implementing the SimpleTasks feature for OPI (ORCA Python Interface).
Please read the attached design spec: simple_tasks_design_spec.md

Also read these already implemented files:
- src/opi/simple_tasks/base.py
- src/opi/simple_tasks/method_params.py

Also read:
- src/opi/output/core.py   (Output class — check available getter methods)

Now implement src/opi/simple_tasks/results.py containing:
- SinglePointCompleted  → primary_property: float  (final energy in Hartree)
- OptCompleted          → primary_property: Structure  (optimised geometry)
- EnGradCompleted       → primary_property: tuple[float, ...]  (energy + gradient)

Each must have a clearly documented primary_property with type and units in
the docstring. Use get_output() to access the Output object — do not
reach into the calculator directly.

When done, confirm which Output getter methods you used so we can verify
they exist.
```

---

## Session 4 — `tasks.py` ✓ DONE

```
I am implementing the SimpleTasks feature for OPI (ORCA Python Interface).
Please read the attached design spec: simple_tasks_design_spec.md

Also read these already implemented files:
- src/opi/simple_tasks/base.py
- src/opi/simple_tasks/method_params.py
- src/opi/simple_tasks/results.py

Now implement src/opi/simple_tasks/tasks.py containing:
- SinglePointTask(Task) → run() returns SinglePointCompleted
- OptTask(Task)         → run() returns OptCompleted
- EnGradTask(Task)      → run() returns EnGradCompleted

The run() implementation logic lives on the base Task class.
Subclasses only need to:
1. Narrow the return type annotation
2. Instantiate the correct TaskCompleted subclass

Add class-level docstrings explaining what each task does and what its
primary property is.
```

---

## Session 5 — `__init__.py` ✓ DONE

```
I am implementing the SimpleTasks feature for OPI (ORCA Python Interface).
Please read the attached design spec: simple_tasks_design_spec.md

All implementation files are now complete:
- src/opi/simple_tasks/base.py
- src/opi/simple_tasks/method_params.py
- src/opi/simple_tasks/results.py
- src/opi/simple_tasks/tasks.py

Now implement src/opi/simple_tasks/__init__.py with the public exports
as specified in the design doc.

Then run the full OPI test suite (nox -s tests) and fix any import errors
or breakage. Do not change existing OPI files unless absolutely necessary —
we are adding, not modifying.

Finally, write a minimal smoke test in tests/simple_tasks/test_smoke.py
that instantiates each task type and calls get_input() to verify the
Input object is assembled correctly — without actually running ORCA.
```

---

## Review checklist (after every session)

Before moving to the next session, verify:

- [ ] Type hints are correct throughout (`str | SimpleKeyword`, `Path | None` etc.)
- [ ] NumPy-style docstrings on all public classes and methods
- [ ] `reuse_completed` guard checks both file existence AND `terminated_normally()`
- [ ] `run()` writes no state back to `self`
- [ ] `get_input()` builds a fresh Input every call (JIT)
- [ ] `nox -s tests` passes with no new failures
- [ ] `mypy` passes on the new file
- [ ] Unknown method strings produce a `warnings.warn`, not a crash
