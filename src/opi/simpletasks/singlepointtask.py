import typing

from opi.input.simple_keywords import SimpleKeyword, Solvent, Task
from opi.simpletasks.base_task import SimpleTask, TaskResults, TaskSettings
from opi.simpletasks.method_settings import MethodSettings


class SinglePointSettings(TaskSettings):
    """Task settings for a single-point energy calculation (``! SP``)."""

    _name: str = "singlepoint"
    task_keyword: typing.Annotated[SimpleKeyword, Task] = Task.SP


class SinglePointResults(TaskResults):
    """Results from a single-point energy calculation."""

    @property
    def final_energy(self) -> float:
        """
        Total energy of the last SCF cycle in Hartree.

        Raises
        ------
        ValueError
            If the energy is not present in the ORCA output.
        """
        final_energy = self.output.get_final_energy()

        if final_energy is None:
            raise ValueError("Could not get final energy from ORCA Output")

        return final_energy

    @property
    def primary_property(self) -> float:
        """Alias for ``final_energy``."""
        return float(self.final_energy)


class SinglePointTask(SimpleTask[SinglePointResults]):
    """
    High-level task for single-point energy calculations.

    Configures ORCA with the ``SP`` keyword and returns a
    ``SinglePointResults`` object whose ``final_energy`` attribute holds the
    total energy in Hartree.
    """

    _task_settings: SinglePointSettings
    _results_type = SinglePointResults

    def __init__(
        self,
        method: str | SimpleKeyword | None = None,
        basis_set: str | SimpleKeyword | None = None,
        solvation_model: str | SimpleKeyword | None = None,
        solvent: str | Solvent | None = None,
        task_settings: SinglePointSettings | None = None,
        method_settings: MethodSettings | None = None,
    ):
        super().__init__(
            method, basis_set, solvation_model, solvent, task_settings, method_settings
        )
