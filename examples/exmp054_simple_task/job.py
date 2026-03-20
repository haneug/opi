#!/usr/bin/env python3
"""Single-point energy calculation using the high-level SimpleTasks interface.

This example shows how to run a B3LYP/def2-SVP single-point calculation on
water using :class:`~opi.simple_tasks.SinglePointTask` instead of assembling
a :class:`~opi.core.Calculator` manually.

The primary result is the final total electronic energy in Hartree, returned
directly by ``result.primary_property``.
"""

import shutil
import sys
from pathlib import Path

from opi.input.structures import Structure
from opi.simple_tasks import SinglePointTask
from opi.simple_tasks.results import SinglePointCompleted


def run_exmp054(
    structure: Structure | None = None,
    working_dir: Path | None = Path("RUN"),
) -> SinglePointCompleted:
    # > recreate the working dir
    shutil.rmtree(working_dir, ignore_errors=True)

    # > if no structure is given read structure from inp.xyz
    if structure is None:
        structure = Structure.from_xyz("inp.xyz")

    # > create the task — method and basis set are the only required inputs
    task = SinglePointTask(method="B3LYP", basis_set="def2-SVP")

    # > run the calculation; working_dir is created automatically
    result = task.run(basename="job", structure=structure, working_dir=working_dir)

    if not result.status:
        print("Calculation did not complete successfully.")
        sys.exit(1)

    energy = result.primary_property
    print(f"Final single-point energy: {energy:.10f} Eh")

    return result


if __name__ == "__main__":
    run_exmp054()
