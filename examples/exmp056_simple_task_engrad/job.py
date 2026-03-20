#!/usr/bin/env python3
"""Energy and gradient calculation using the high-level SimpleTasks interface.

This example shows how to run a B3LYP/def2-SVP energy and gradient calculation
on water using :class:`~opi.simple_tasks.EnGradTask`.

The primary result is a ``(energy, gradient)`` tuple returned directly by
``result.primary_property``, where *energy* is the total electronic energy in
Hartree and *gradient* is a flat tuple of Cartesian gradient components
(x, y, z per atom) in Eh/Bohr.
"""

import shutil
import sys
from pathlib import Path

from opi.input.structures import Structure
from opi.simple_tasks import EnGradTask
from opi.simple_tasks.results import EnGradCompleted


def run_exmp056(
    structure: Structure | None = None,
    working_dir: Path | None = Path("RUN"),
) -> EnGradCompleted:
    # > recreate the working dir
    shutil.rmtree(working_dir, ignore_errors=True)

    # > if no structure is given read structure from inp.xyz
    if structure is None:
        structure = Structure.from_xyz("inp.xyz")

    # > create the task
    task = EnGradTask(method="B3LYP", basis_set="def2-SVP")

    # > run the calculation; working_dir is created automatically
    result = task.run(basename="job", structure=structure, working_dir=working_dir)

    if not result.status:
        print("Calculation did not complete successfully.")
        sys.exit(1)

    energy, gradient = result.primary_property
    print(f"Final energy: {energy:.10f} Eh")
    print(f"Gradient norm (Eh/Bohr): {sum(g**2 for g in gradient) ** 0.5:.6f}")

    return result


if __name__ == "__main__":
    run_exmp056()
