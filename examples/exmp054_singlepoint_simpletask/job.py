#!/usr/bin/env python3
import sys
from pathlib import Path

from opi.input.structures import Structure
from opi.simpletasks.singlepointtask import SinglePointResults, SinglePointTask


def run_exmp054(
    structure: Structure | None = None, working_dir: Path = Path("RUN")
) -> SinglePointResults:
    # > if no structure is given read structure from inp.xyz
    if structure is None:
        structure = Structure.from_xyz("inp.xyz")

    # > set up the task
    simple_task = SinglePointTask(
        method="b3lyp", basis_set="def2-svp", solvation_model="cpcm", solvent="water"
    )
    # > there are task and method-specific settings, these can be set through kwargs

    # > run the calculation with given data
    singlepoint_result = simple_task.run("job", structure, working_dir=working_dir)

    # > check if the ORCA calculation terminated normally
    if not singlepoint_result.status:
        print("SinglePoint task failed")
        sys.exit(1)

    # > extract final energy from the `TaskResults` object
    final_energy = singlepoint_result.final_energy

    print(f"Final single point energy: {final_energy: 10f} Eh")

    return singlepoint_result


if __name__ == "__main__":
    run_exmp054()
