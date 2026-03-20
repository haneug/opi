#!/usr/bin/env python3
"""Geometry optimisation using the high-level SimpleTasks interface.

This example shows how to run a B3LYP/def2-SVP geometry optimisation on
water using :class:`~opi.simple_tasks.OptTask`.

The primary result is a ``(energy, structure)`` tuple returned directly by
``result.primary_property``, where *energy* is the final total electronic
energy in Hartree and *structure* is the optimised geometry.
"""

import shutil
import sys
from pathlib import Path

from opi.input.structures import Structure
from opi.simple_tasks import OptTask
from opi.simple_tasks.results import OptCompleted


def run_exmp055(
    structure: Structure | None = None,
    working_dir: Path | None = Path("RUN"),
) -> OptCompleted:
    # > recreate the working dir
    shutil.rmtree(working_dir, ignore_errors=True)

    # > if no structure is given read structure from inp.xyz
    if structure is None:
        structure = Structure.from_xyz("inp.xyz")

    # > create the task
    task = OptTask(method="B3LYP", basis_set="def2-SVP")

    # > run the calculation; working_dir is created automatically
    result = task.run(basename="job", structure=structure, working_dir=working_dir)

    if not result.status:
        print("Calculation did not complete successfully.")
        sys.exit(1)

    energy, optimised_structure = result.primary_property
    print(f"Final energy:          {energy:.10f} Eh")
    print(f"Optimised structure:   {len(optimised_structure.atoms)} atoms")

    return result


if __name__ == "__main__":
    run_exmp055()
